import json
import re

import aiohttp

from .exceptions import PixivoAuthException
from .httpclient import HttpClient


class PixivoLogin(HttpClient):

    def __init__(self, pixiv_id, password):
        super().__init__()

        self.pixiv_id = pixiv_id
        self.password = password

        self.post_key = None

    async def __getPostKey(self):
        login_url = 'https://accounts.pixiv.net/login?lang=zh'
        async with self.request(login_url) as resp:
            pkey_pattern = re.compile(r'name="post_key" value="([0-9a-f]+)"')
            html = await resp.text()
            re_result = re.search(pkey_pattern, html)
            if re_result:
                self.post_key = re_result.group(1)
            else:
                raise PixivoAuthException('Can\'t get post_key on this page!')

    async def login(self):
        await self.__getPostKey()
        login_api_url = 'https://accounts.pixiv.net/api/login?lang=zh'
        post_data = {
            'password':	self.password,
            'pixiv_id':	self.pixiv_id,
            'post_key':	self.post_key,
            'ref': 'wwwtop_accounts_index',
            'return_to': 'https://www.pixiv.net/',
            'source': 'pc'
        }
        headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'Host': 'accounts.pixiv.net',
            'Referer': 'https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index'
        }
        async with self.request(login_api_url, 'POST', headers, post_data) as resp:
            try:
                text = await resp.text()
                res_json = json.loads(text)
                if res_json['error']:
                    raise PixivoAuthException(res_json['message'])
                else:
                    res_body = res_json['body']
                    if 'success' in res_body:
                        self._save_cookies()
                        print('Login at pixiv successfully!')
                    elif 'validation_errors' in res_body:
                        validation_errors = res_body['validation_errors']
                        raise PixivoAuthException(validation_errors)
                    else:
                        print(res_body)
                res_body = res_json['body']

            except json.decoder.JSONDecodeError:
                raise PixivoAuthException(
                    'Response must be in the json format !')


class PixivoAuth(HttpClient):

    def __init__(self):
        super().__init__()

    async def checkLogin(self):
        async with self.request('https://www.pixiv.net') as resp:
            html = await resp.text()
            loggined_pattern = re.compile(r'pixiv.user.loggedIn = true;')
            if not re.search(loggined_pattern, html):
                raise PixivoAuthException('Please login the pixiv!')
            print('Login successfully!')
            self._save_cookies()

    async def getContextToken(self):
        async with self.request('https://www.pixiv.net') as resp:
            html = await resp.text()
            token_pattern = re.compile(r'pixiv.context.token = "([0-9a-f]+)";')
            loggined_pattern = re.compile(r'pixiv.user.loggedIn = true;')
            if not re.search(loggined_pattern, html):
                raise PixivoAuthException('Please login the pixiv!')
            re_res = re.search(token_pattern, html)
            if not re_res:
                raise PixivoAuthException('Can not get the context token!')
            context_token = re_res.group(1)
            print('pixiv.context.token = "%s";' % context_token)
            self._save_cookies()
            return context_token
        return None
