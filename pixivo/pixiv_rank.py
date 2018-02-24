import datetime
import json
import re
import time

import yaml
from pytz import timezone

from .database import PixivoDatabase
from .exceptions import PixivoSpiderException
from .httpclient import HttpClient
from .pixiv_auth import PixivoAuth


class PixivoRankSpider(HttpClient):

    def __init__(self):
        super().__init__()
        self.auth = PixivoAuth()

        self.context_token = None

        self.data_base = PixivoDatabase()

        with open('_config.yml') as fp:
            config = yaml.load(fp)
            r18 = config['r18'] if config['r18'] == True else False
            self.content_type = config['type'] or 'all'
            if self.content_type not in ['all', 'illust', 'manga', 'ugoira']:
                raise PixivoSpiderException(
                    'Can\'t got the "%s" ranking from pixiv!' % self.content_type
                )
            self.date_str = config['date']
            if not self.date_str:
                today = datetime.datetime.now()
                today = today.astimezone(timezone('Japan'))
                yesterday = today - datetime.timedelta(days=1)
                self.date_str = yesterday.strftime('%Y%m%d')
            self.mode = 'daily'
            if r18:
                self.mode = 'daily_r18'

    async def __getRanking(self, page):
        rank_url = 'https://www.pixiv.net/ranking.php?mode={}{}&p={}&date={}&format=json&tt={}'\
            .format(
                self.mode,
                '&content={}'.format(self.content_type)
                if self.content_type != 'all' else '',
                page,
                self.date_str,
                self.context_token
            )
        async with self.request(rank_url, timeout=None) as resp:
            text = await resp.text()
            try:
                res_json = json.loads(text)
                if 'error' in res_json:
                    raise PixivoSpiderException(res_json['error'])
                ranks = res_json['contents']
                for illust in ranks:
                    illust_id = illust['illust_id']
                    user_id = illust['user_id']
                    user_name = illust['user_name']
                    tags = illust['tags']
                    print('''
rank: {}
illust_id: {}
title: {}
user_name: {}
tags: {}'''.format(illust['rank'], illust_id, illust['title'], user_name, tags))
                    if not self.data_base.exist_illust(illust_id):
                        self.data_base.insert_illust(illust)
                    else:
                        self.data_base.update_illust(illust_id, illust)
                    if not self.data_base.exist_user(user_id):
                        self.data_base.insert_user(user_id, user_name)
                    else:
                        self.data_base.update_user(user_id, user_name)
                return res_json['next']
            except json.decoder.JSONDecodeError:
                raise PixivoSpiderException(
                    'Please confirm your configs in _config.yml.')

        return False

    async def getRankingList(self):
        self.context_token = await self.auth.getContextToken()
        print('Spider config:')
        print('- Mode: {}'.format(self.mode))
        print('- Date: {}'.format(self.date_str))
        print('- Type: {}'.format(self.content_type))
        page = 1
        page = await self.__getRanking(page)
        start = time.time()
        while page:
            page = await self.__getRanking(page)
        print()
        print('Finished in {} s!'.format(time.time() - start))
