import json
import os
import sqlite3
import time

import yaml

from .exceptions import PixivoDBException


class PixivoDatabase:

    def __init__(self):
        with open('_config.yml') as fp:
            config = yaml.load(fp)
            self.path = config['path']
            self.db_path = os.path.join(self.path, 'data.db')

        self.timestamp = int(time.time())

        self.db_conn = sqlite3.connect(self.db_path)
        self.db_cur = self.db_conn.cursor()

        self.__init_db()

    def __init_db(self):
        if not self.__exist_table('ILLUST'):
            self.db_cur.execute('''
            CREATE TABLE ILLUST(
                ID          INTEGER PRIMARY KEY,
                TYPE        INTEGER,
                TITLE       TEXT,
                DATE        INTEGER,
                PAGE        INTEGER,
                USER        INTEGER,
                TAGS        TEXT,
                RATING      INTEGER,
                VIEW        INTEGER,
                TIME        INTEGER,
                STATUS      INTEGER DEFAULT 0
            );''')
        if not self.__exist_table('USER'):
            self.db_cur.execute('''
            CREATE TABLE USER(
                ID          INTEGER PRIMARY KEY,
                NAME        TEXT,
                TIME        INTEGER
            );''')
        if not self.__exist_table('FILE'):
            self.db_cur.execute('''
            CREATE TABLE FILE(
                IID         INTEGER,
                REF         TEXT PRIMARY KEY,
                URL         TEXT,
                TYPE        INTEGER,
                STATUS      INTEGER DEFAULT 0,
                PATH        TEXT
            );''')
        self.db_conn.commit()

    def __exist_table(self, table_name):
        self.db_cur.execute(
            'SELECT COUNT(*) FROM SQLITE_MASTER WHERE TYPE=? AND NAME=?;',
            ('table', table_name)
        )
        return self.db_cur.fetchone()[0] != 0

    def exist_illust(self, illust_id):
        self.db_cur.execute('''
        SELECT COUNT(*) FROM ILLUST WHERE ID=?;
        ''', (illust_id,))
        return self.db_cur.fetchone()[0] != 0

    def insert_illust(self, illust_info):
        illust_id = illust_info['illust_id']
        illust_type = int(illust_info['illust_type'])
        illust_title = illust_info['title']
        timestamp = illust_info['illust_upload_timestamp']
        page_count = int(illust_info['illust_page_count'])
        user_id = illust_info['user_id']
        tags = json.dumps(illust_info['tags'], ensure_ascii=False)
        rating_count = illust_info['rating_count']
        view_count = illust_info['view_count']
        self.db_cur.execute('''
        INSERT INTO ILLUST (ID,TYPE,TITLE,DATE,PAGE,USER,TAGS,RATING,VIEW,TIME)
        VALUES (?,?,?,?,?,?,?,?,?,?);
        ''', (illust_id, illust_type, illust_title, timestamp, page_count,
              user_id, tags, rating_count, view_count, self.timestamp))
        self.db_conn.commit()

    def update_illust(self, illust_id, illust_info):
        illust_type = int(illust_info['illust_type'])
        illust_title = illust_info['title']
        tags = json.dumps(illust_info['tags'], ensure_ascii=False)
        timestamp = illust_info['illust_upload_timestamp']
        page_count = int(illust_info['illust_page_count'])
        user_id = illust_info['user_id']
        rating_count = illust_info['rating_count']
        view_count = illust_info['view_count']
        self.db_cur.execute(
            'UPDATE ILLUST SET TYPE = ?,TITLE = ?,DATE = ?,PAGE = ?,USER = ?,TAGS = ?,RATING = ?,VIEW = ?, TIME = ? WHERE ID = ?;',
            (illust_type, illust_title, timestamp, page_count, user_id,
             tags, rating_count, view_count, self.timestamp, illust_id)
        )
        self.db_conn.commit()

    def set_illust_status(self, illust_id, status=1):
        self.db_cur.execute(
            'UPDATE ILLUST SET STATUS = ? WHERE ID = ?;',
            (status, illust_id)
        )
        self.db_conn.commit()

    def get_unset_illust(self):
        limit = 100
        self.db_cur.execute(
            'SELECT ID, TYPE, PAGE FROM ILLUST WHERE STATUS = 0 LIMIT ?;',
            (limit,)
        )
        return self.db_cur.fetchall()

    def exist_user(self, user_id):
        self.db_cur.execute(
            'SELECT COUNT(*) FROM USER WHERE ID=?;', (user_id,))
        return self.db_cur.fetchone()[0] != 0

    def insert_user(self, user_id, user_name):
        self.db_cur.execute(
            'INSERT INTO USER (ID,NAME,TIME) VALUES (?,?,?);',
            (user_id, user_name, self.timestamp)
        )
        self.db_conn.commit()

    def update_user(self, user_id, user_name):
        self.db_cur.execute(
            'UPDATE USER SET NAME = ?, TIME = ? WHERE ID = ?;',
            (user_name, self.timestamp, user_id)
        )
        self.db_conn.commit()

    def exsit_file(self, illust_id):
        self.db_cur.execute(
            'SELECT COUNT(*) FROM FILE WHERE IID=?;', (illust_id,))
        return self.db_cur.fetchone()[0] != 0

    def insert_illust_file(self, illust_id, illust_type, ref_url):
        self.db_cur.execute(
            'INSERT INTO FILE (IID,TYPE,REF) VALUES (?,?,?);',
            (illust_id, illust_type, ref_url)
        )
        self.db_conn.commit()

    def insert_manga_file(self, manga_id, base_ref_url, page_count):
        manga_pages = []
        for p in range(page_count):
            manga_pages.append(
                (manga_id, base_ref_url + '&page={}'.format(p))
            )
        self.db_cur.executemany(
            'INSERT INTO FILE (IID,TYPE,REF) VALUES (?,1,?);',
            manga_pages
        )
        self.db_conn.commit()

    def count_file(self, illust_id):
        self.db_cur.execute(
            'SELECT COUNT(*) FROM FILE WHERE STATUS=0 AND IID=?;', (illust_id,))
        return self.db_cur.fetchone()[0]

    def get_unset_files(self):
        limit = 10
        self.db_cur.execute(
            'SELECT IID, TYPE, REF, URL, PATH FROM FILE WHERE STATUS = 0 LIMIT ?;',
            (limit,)
        )
        return self.db_cur.fetchall()

    def count_unset_files(self):
        self.db_cur.execute('SELECT COUNT(*) FROM FILE WHERE STATUS=0;')
        return self.db_cur.fetchone()[0]

    def set_file(self, ref, url, path):
        self.db_cur.execute(
            'UPDATE FILE SET URL = ?, PATH = ? WHERE REF = ?;',
            (url, path, ref)
        )
        self.db_conn.commit()

    def set_file_status(self, ref, status=0):
        self.db_cur.execute(
            'UPDATE FILE SET STATUS = ? WHERE REF = ?;',
            (status, ref)
        )
        self.db_conn.commit()

    def get_illust_status(self, illust_id):
        self.db_cur.execute(
            'SELECT STATUS FROM ILLUST WHERE ID=?;', (illust_id,))
        res = self.db_cur.fetchone()
        return res[0] if res else -1

    def get_illust_info(self, illust_id):
        self.db_cur.execute(
            '''SELECT TITLE,DATE,USER.NAME,USER.ID,PAGE,TAGS,RATING,VIEW FROM ILLUST
            INNER JOIN USER ON USER.ID = ILLUST.USER
            WHERE ILLUST.ID=?;''',
            (illust_id,))
        res = self.db_cur.fetchone()
        return res

    def get_files_for_illust(self, illust_id):
        self.db_cur.execute(
            'SELECT PATH FROM FILE WHERE IID=? AND STATUS = 1;', (illust_id,))
        res = self.db_cur.fetchall()
        return res

    def get_illust_info_by_user_id(self, user_id, page=1):
        limit = 10
        skip = (page - 1) * limit
        self.db_cur.execute(
            'SELECT ID,TITLE,DATE,PAGE,TAGS,RATING,VIEW FROM ILLUST WHERE USER=? ORDER BY RATING DESC LIMIT ?,?;',
            (user_id, skip, limit))
        res = self.db_cur.fetchall()
        return res

    def get_user_name(self, user_id):
        self.db_cur.execute(
            'SELECT NAME FROM USER WHERE ID=?;',
            (user_id,)
        )
        res = self.db_cur.fetchone()
        return res[0] if res and res[0] else str(user_id)

    def get_user_by_name(self, user_name, page=1):
        limit = 10
        skip = (page - 1) * limit
        self.db_cur.execute(
            'SELECT ID,NAME FROM USER WHERE NAME LIKE ? LIMIT ?,?;',
            ('%' + user_name + '%', skip, limit)
        )
        return self.db_cur.fetchall()

    def get_illust_info_by_keyword(self, keyword, page=1):
        limit = 10
        skip = (page - 1) * limit
        self.db_cur.execute(
            '''SELECT ILLUST.ID,TITLE,DATE,USER.NAME,USER.ID,PAGE,TAGS,RATING,VIEW FROM ILLUST
            INNER JOIN USER ON USER.ID = ILLUST.USER
            WHERE TITLE LIKE ? OR TAGS LIKE ?
            ORDER BY RATING DESC
            LIMIT ?,?;''',
            ('%' + keyword + '%', '%' + keyword + '%', skip, limit))
        res = self.db_cur.fetchall()
        return res

    def __del__(self):
        self.db_conn.close()
