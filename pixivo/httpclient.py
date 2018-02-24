import os

import aiohttp
import yaml


class HttpClient:

    def __init__(self):
        with open('_config.yml') as fp:
            config = yaml.load(fp)
            self.proxy = config['proxy'] if 'proxy' in config else None
            self.path = config['path']

        conn = aiohttp.TCPConnector(
            verify_ssl=False,
            use_dns_cache=True,
            force_close=True
        )

        self.cookie_path = os.path.join(self.path, 'cookie')
        jar = aiohttp.CookieJar()
        if os.path.isfile(self.cookie_path):
            try:
                jar.load(self.cookie_path)
            except EOFError:
                pass

        self.session = aiohttp.ClientSession(
            connector=conn, cookie_jar=jar)

    def __del__(self):
        self.session.connector.close()

    def _save_cookies(self):
        self.session.cookie_jar.save(self.cookie_path)

    def request(self, url, method='GET', headers={}, data=None, timeout=25):
        _headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; ServiceUI 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299'
        }
        _headers.update(headers)
        return self.session.request(
            method,
            url,
            headers=_headers,
            data=data,
            proxy=self.proxy,
            timeout=timeout
        )
