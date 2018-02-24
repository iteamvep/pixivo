import os
import json
import time
import sys
import shutil
import yaml

from .database import PixivoDatabase


class PixivoSearcher:

    def __init__(self):
        with open('_config.yml') as fp:
            config = yaml.load(fp)
            self.result_path = config['r_path']

        if os.path.isdir(self.result_path):
            old_results = os.listdir(self.result_path)
            if old_results:
                sel = input(
                    'Result path is not empty. {} files is found.\n> Do you want to clear?[y/n]'
                    .format(len(old_results)))
                sel = sel.lower()
                if sel == 'y':
                    for old_result in old_results:
                        os.remove(os.path.join(self.result_path, old_result))
                    print('Result path cleared.')
        else:
            os.mkdir(self.result_path)
            print('Result path created.')
        print('The result path is {}/. Where all output files will be placed.'
              .format(self.result_path))
        self.data_base = PixivoDatabase()

    def searchIllustId(self, illust_id):
        illust_status = self.data_base.get_illust_status(illust_id)
        if illust_status == -1:
            print('No data for illust id = {}!'.format(illust_id))
            sys.exit(0)
        elif illust_status != 2:
            print('Files of illust id = {} is not prepared!'.format(illust_id))
            sys.exit(0)
        sel = input(
            '> Do you want to copy the results to the result path?[y/n]')
        sel = sel.lower()
        illust_info = self.data_base.get_illust_info(illust_id)
        print('=' * 3 + 'Result' + '=' * 3)
        print('ID: \t{}'.format(illust_id))
        print('Title: \t' + illust_info[0])
        st = time.localtime(illust_info[1])
        print('Time: \t' + time.strftime('%Y-%m-%d %H:%M:%S', st))
        print('User: \t{}(id={})'.format(illust_info[2], illust_info[3]))
        print('Pages: \t{}'.format(illust_info[4]))
        print('Tags: \t{}'.format('、'.join(json.loads(illust_info[5]))))
        print('Rate: \t{}'.format(illust_info[6]))
        print('View: \t{}'.format(illust_info[7]))
        print('=' * 12)
        if sel == 'y':
            files = self.data_base.get_files_for_illust(illust_id)
            for file in files:
                base_name = os.path.basename(file[0])
                shutil.copy(
                    file[0],
                    os.path.join(self.result_path,
                                 '{}_{}'.format(illust_id, base_name))
                )
            print('All results are copied to the result path.')

    def searchUserId(self, user_id):
        if not self.data_base.exist_user(user_id):
            print('No data for user id = {}!'.format(user_id))
            sys.exit(0)
        sel = input(
            '> Do you want to copy the results to the result path?[y/n]')
        sel = sel.lower()
        user_name = self.data_base.get_user_name(user_id)
        print('*' * 3 + 'Result' + '*' * 3)
        print('ID: \t{}'.format(user_id))
        print('NAME: \t' + user_name)
        print('*' * 12)
        page = 1
        works = self.data_base.get_illust_info_by_user_id(user_id, page)
        num = 0
        while works:
            for work in works:
                num += 1
                print('=' * 12)
                print('ID: \t{}'.format(work[0]))
                print('Title: \t' + work[1])
                st = time.localtime(work[2])
                print('Time: \t' + time.strftime('%Y-%m-%d %H:%M:%S', st))
                print('User: \t{}(id={})'.format(
                    user_name, user_id))
                print('Pages: \t{}'.format(work[3]))
                print('Tags: \t{}'.format(
                    '、'.join(json.loads(work[4]))))
                print('Rate: \t{}'.format(work[5]))
                print('View: \t{}'.format(work[6]))
                print('=' * 12)
                if sel == 'y':
                    files = self.data_base.get_files_for_illust(work[0])
                    for file in files:
                        base_name = os.path.basename(file[0])
                        shutil.copy(
                            file[0],
                            os.path.join(self.result_path,
                                         '{}_{}_{}'.format(num, work[0], base_name))
                        )
            page += 1
            works = self.data_base.get_illust_info_by_user_id(user_id, page)
            input('Press Enter to continue.')
        print('All results is presented!')
        if sel == 'y':
            print('All results are copied to the result path.')

    def searchUsername(self, u_name):
        page = 1
        users = self.data_base.get_user_by_name(u_name, page)
        if not users:
            print('No results from the database.')
            sys.exit(0)
        num = 0
        while users:
            for user in users:
                num += 1
                print()
                print('No.{}'.format(num))
                print('ID: \t{}'.format(user[0]))
                print('NAME: \t' + user[1])
            page += 1
            users = self.data_base.get_user_by_name(u_name, page)
            input('Press Enter to continue.')

    def searchTitleAndTags(self, keyword):
        page = 1
        works = self.data_base.get_illust_info_by_keyword(keyword, page)
        if not works:
            print('No results from the database.')
            sys.exit(0)
        sel = input(
            '> Do you want to copy the results to the result path?[y/n]')
        sel = sel.lower()
        num = 0
        while works:
            for work in works:
                num += 1
                print()
                print('ID: \t{}'.format(work[0]))
                print('Title: \t' + work[1])
                st = time.localtime(work[2])
                print('Time: \t' + time.strftime('%Y-%m-%d %H:%M:%S', st))
                print('User: \t{}(id={})'.format(
                    work[3], work[4]))
                print('Pages: \t{}'.format(work[5]))
                print('Tags: \t{}'.format(
                    '、'.join(json.loads(work[6]))))
                print('Rate: \t{}'.format(work[7]))
                print('View: \t{}'.format(work[8]))
                if sel == 'y':
                    files = self.data_base.get_files_for_illust(work[0])
                    for file in files:
                        base_name = os.path.basename(file[0])
                        shutil.copy(
                            file[0],
                            os.path.join(self.result_path,
                                         '{}_{}_{}'.format(num, work[0], base_name))
                        )
            page += 1
            works = self.data_base.get_illust_info_by_keyword(keyword, page)
            input('Press Enter to continue.')
        print('All results is presented!')
        if sel == 'y':
            print('All results are copied to the result path.')
