import asyncio
import json
import os
import re
import shutil
import sys
import time
from zipfile import ZipFile

import aiohttp
import imageio
import lxml
import yaml
from bs4 import BeautifulSoup

from .database import PixivoDatabase
from .httpclient import HttpClient
from .pixiv_auth import PixivoAuth


class PixivoDownloader(HttpClient):
    ugoira_info_pattern = re.compile(
        r'pixiv.context.ugokuIllustFullscreenData  = ({\S+});')

    def __init__(self):
        super().__init__()
        self.auth = PixivoAuth()
        self.data_base = PixivoDatabase()
        self.__init_dld()

    def __init_dld(self):
        print('Initializing files....')
        unsets = self.data_base.get_unset_illust()
        while unsets:
            for illust_id, illust_type, illust_page in unsets:
                if self.data_base.exsit_file(illust_id):
                    continue

                base_ref_url = 'https://www.pixiv.net/member_illust.php?mode=%s&illust_id=%d'

                if illust_type == 0:
                    if illust_page > 1:
                        ref_url = base_ref_url % ('manga_big', illust_id)
                        self.data_base.insert_manga_file(
                            illust_id, ref_url, illust_page)
                        print('id: {}\ntype: illust(manga)\ncount: {}\n'.format(
                            illust_id, illust_page))
                    else:
                        ref_url = base_ref_url % ('medium', illust_id)
                        self.data_base.insert_illust_file(
                            illust_id, 0, ref_url)
                        print('id: {}\ntype: illust\ncount: 1\n'.format(illust_id))
                elif illust_type == 1:
                    ref_url = base_ref_url % ('manga_big', illust_id)
                    self.data_base.insert_manga_file(
                        illust_id, ref_url, illust_page)
                    print('id: {}\ntype: manga\ncount: {}\n'.format(
                        illust_id, illust_page))
                elif illust_type == 2:
                    ref_url = base_ref_url % ('medium', illust_id)
                    self.data_base.insert_illust_file(illust_id, 2, ref_url)
                    print('id: {}\ntype: ugoira\ncount: 1\n'.format(illust_id))
                self.data_base.set_illust_status(illust_id)
            unsets = self.data_base.get_unset_illust()
        print('Files initialized successfully!')

    async def downloadIllust(self, illust_id, origin_url, src_url, dl_path):
        if not src_url:
            try:
                resp = await self.request(origin_url)
                html = await resp.text()
                soup = BeautifulSoup(html, 'lxml')
                src_url = soup.select_one(
                    'img.original-image').attrs['data-src']
                ext_name = os.path.splitext(src_url)[1]
                file_name = 'p0%s' % ext_name
                file_path = os.path.join(self.path, 'illust', str(illust_id))
                os.makedirs(file_path, exist_ok=True)
                dl_path = os.path.join(file_path, file_name)
                self.data_base.set_file(origin_url, src_url, dl_path)
            except Exception as err:
                sys.stdout.write(
                    'resolve {} -x> Boom!\n'.format(illust_id))
                print(err)
                sys.stdout.flush()
                return
        resp = None
        base_name = os.path.basename(src_url)
        try:
            resp = await self.request(src_url, headers={'Referer': origin_url})
            with open(dl_path, 'wb') as fp:
                while True:
                    chunk = await resp.content.readany()
                    if not chunk:
                        break
                    fp.write(chunk)
                sys.stdout.write(
                    '{} --> OK!\n{} Saved!\n'.format(base_name, dl_path))
                sys.stdout.flush()
                self.data_base.set_file_status(origin_url, 1)
                self.data_base.set_illust_status(illust_id, 2)
        except Exception:
            if os.path.isfile(dl_path):
                os.remove(dl_path)
            sys.stdout.write(
                '{} -x> Error!\n'.format(base_name))
            sys.stdout.flush()
        finally:
            if resp:
                resp.close()

    async def downloadMangaPage(self, illust_id, origin_url, src_url, dl_path):
        if not src_url:
            try:
                resp = await self.request(origin_url)
                html = await resp.text()
                soup = BeautifulSoup(html, 'lxml')
                img = soup.select_one(
                    'body > img')
                if not img:
                    self.data_base.set_file_status(origin_url, 2)
                    sys.stdout.write(
                        'resolve {} -x> Wrong!\n'.format(illust_id))
                    sys.stdout.flush()
                    return
                src_url = img.attrs['src']
                base_name = os.path.basename(src_url)
                iid = str(illust_id)
                file_name = base_name.replace(iid + '_', '')
                file_path = os.path.join(self.path, 'manga', iid)
                os.makedirs(file_path, exist_ok=True)
                dl_path = os.path.join(file_path, file_name)
                self.data_base.set_file(origin_url, src_url, dl_path)
            except Exception as err:
                sys.stdout.write(
                    'resolve {} -x> Boom!\n'.format(illust_id))
                print(err)
                sys.stdout.flush()
                return
        resp = None
        base_name = os.path.basename(src_url)
        try:
            resp = await self.request(src_url, headers={'Referer': origin_url})
            with open(dl_path, 'wb') as fp:
                while True:
                    chunk = await resp.content.readany()
                    if not chunk:
                        break
                    fp.write(chunk)
                sys.stdout.write(
                    '{} --> OK!\n{} Saved!\n'.format(base_name, dl_path))
                sys.stdout.flush()
                self.data_base.set_file_status(origin_url, 1)
                if not self.data_base.count_file(illust_id):
                    self.data_base.set_illust_status(illust_id, 2)
        except Exception:
            if os.path.isfile(dl_path):
                os.remove(dl_path)
            sys.stdout.write(
                '{} -x> Error!\n'.format(base_name))
            sys.stdout.flush()
        finally:
            if resp:
                resp.close()

    async def downloadUgoira(self, illust_id, origin_url, src_url, dl_path):
        file_path = os.path.join(self.path, 'ugoira', str(illust_id))
        if not src_url:
            try:
                resp = await self.request(origin_url)
                html = await resp.text()
                result = re.search(self.ugoira_info_pattern, html).group(1)
                ugoira_info = json.loads(result)
                src_url = ugoira_info['src']
                file_name = os.path.basename(src_url)
                frames_info = ugoira_info['frames']
                os.makedirs(file_path, exist_ok=True)
                dl_path = os.path.join(file_path, file_name)
                fr_path = os.path.join(file_path, 'frames.json')
                with open(fr_path, 'w', encoding='utf-8') as fp:
                    json.dump(frames_info, fp,
                              ensure_ascii=False, sort_keys=True)
                self.data_base.set_file(origin_url, src_url, dl_path)
            except Exception as err:
                sys.stdout.write(
                    'resolve {} -x> Boom!\n'.format(illust_id))
                print(err)
                sys.stdout.flush()
                return
        fr_path = os.path.join(file_path, 'frames.json')
        extract_path = os.path.join(file_path, 'tmp')

        frames_info = []
        with open(fr_path, 'r', encoding='utf-8') as fp:
            frames_info = json.load(fp)
        resp = None
        base_name = os.path.basename(src_url)
        try:
            resp = await self.request(src_url, headers={'Referer': origin_url})
            with open(dl_path, 'wb') as fp:
                while True:
                    chunk = await resp.content.readany()
                    if not chunk:
                        break
                    fp.write(chunk)
                sys.stdout.write(
                    '{} --> OK!\n{} Saved!\n'.format(base_name, dl_path))
                sys.stdout.flush()
            os.makedirs(extract_path, exist_ok=True)
            with ZipFile(dl_path) as zf:
                zf.extractall(extract_path)
            frames = []
            delays = []
            gif_name = os.path.join(file_path, 'p0.gif')
            for frame in frames_info:
                frames.append(imageio.imread(
                    os.path.join(extract_path, frame['file'])))
                delays.append(frame['delay'] / 1000)
            imageio.mimsave(gif_name, frames, 'GIF', duration=delays)
            shutil.rmtree(extract_path)
            if os.path.isfile(dl_path):
                os.remove(dl_path)
            self.data_base.set_file(origin_url, src_url, gif_name)
            self.data_base.set_file_status(origin_url, 1)
            self.data_base.set_illust_status(illust_id, 2)
        except Exception:
            shutil.rmtree(extract_path)
            if os.path.isfile(dl_path):
                os.remove(dl_path)
            sys.stdout.write(
                '{} -x> Error!\n'.format(base_name))
            sys.stdout.flush()
        finally:
            if resp:
                resp.close()

    async def start(self):
        await self.auth.checkLogin()
        st = time.time()
        unset_files = self.data_base.get_unset_files()
        p_count = 1
        while unset_files:
            tot = self.data_base.count_unset_files()
            sys.stdout.write('T{}. Start downloading {} files, total {} files rest...\n'.format(
                p_count, len(unset_files), tot))
            sys.stdout.flush()
            dl_tasks = []
            for illust_id, dl_type, origin_url, src_url, dl_path in unset_files:
                if dl_type == 0:
                    dl_tasks.append(asyncio.ensure_future(
                        self.downloadIllust(
                            illust_id, origin_url, src_url, dl_path)
                    ))
                elif dl_type == 1:
                    dl_tasks.append(asyncio.ensure_future(
                        self.downloadMangaPage(
                            illust_id, origin_url, src_url, dl_path)
                    ))
                elif dl_type == 2:
                    dl_tasks.append(asyncio.ensure_future(
                        self.downloadUgoira(
                            illust_id, origin_url, src_url, dl_path)
                    ))
            await asyncio.gather(* dl_tasks)
            unset_files = self.data_base.get_unset_files()
            p_count += 1
        print()
        print('Finished in {} s!'.format(time.time() - st))
