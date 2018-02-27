#!/usr/bin/env python3
import os
import re
import yaml
from pymongo import MongoClient

from breadbot.core import common


class importData(object):

    def __init__(self):
        self.db = self._open_db()

    def do_import(self, dataPaths=[]):
        print('Start import data...')
        self.all_flag = False
        if not dataPaths:
            dataPaths = common.cfg().get('data_path')
            self.all_flag = True
        self.dataPaths = dataPaths
        redundList = \
            self._get_redund_list()
        self._clean_old_db_data(redundList)
        changedList = \
            self._get_changed_list()
        self._clean_old_db_data(changedList)
        self._import_db_data(changedList)

    def _open_db(self):
        db_name = common.cfg().get('db_name')
        ip = common.cfg().get('db_ip')
        port = common.cfg().get('db_port')
        client = MongoClient(ip, port)
        return client[db_name]

    def _clean_old_db_data(self, dataPaths):
        for dataPath in dataPaths:
            if not dataPath:
                continue
            else:
                coll = self._get_coll_name(dataPath)
                print('clean %s...' % coll)
                self.db[coll].drop()

    def _get_coll_name(self, dataPath):
        return re.sub('[^a-zA-Z0-9]', '_', dataPath)

    def _read_data_file(self, dataPath):
        with open(dataPath, 'r') as f:
            readStr = f.read()
            readStr = re.sub(r'\n +\n', '\n\n', readStr)
        return readStr

    def _get_modify_time(self, dataPath):
        return os.stat(dataPath).st_mtime

    def _get_cur_list(self):
        curList = []
        for dataPath in self.dataPaths:
            if not os.path.exists(dataPath):
                continue
            for root, dirs, files in os.walk(dataPath):
                for file in files:
                    if not re.match(r'^.*\.yml$', file):
                        continue
                    dataPath = os.path.join(root, file)
                    curList.append(dataPath)
        return curList

    def _get_old_list(self):
        colls = self.db.collection_names()
        oldList = []
        for coll in colls:
            if coll[-4:] != '_yml':
                continue
            db_data = self.db[coll].find_one()
            if db_data:
                dataPath = db_data['path']
                if dataPath:
                    oldList.append(dataPath)
        return oldList

    def _get_changed_list(self):
        if not self.all_flag:
            return self.dataPaths
        curList = self._get_cur_list()
        oldList = self._get_old_list()
        changedList = []
        for dataPath in curList:
            coll = self._get_coll_name(dataPath)
            db_data = self.db[coll].find_one()
            if db_data:
                old_mtime = db_data['mtime']
            new_mtime = self._get_modify_time(dataPath)
            if dataPath not in oldList:
                changedList.append(dataPath)
            elif old_mtime != new_mtime:
                changedList.append(dataPath)
        changedList = list(set(changedList))
        return changedList

    def _get_redund_list(self):
        if not self.all_flag:
            return self.dataPaths
        curList = self._get_cur_list()
        oldList = self._get_old_list()
        redundList = []
        for dataPath in oldList:
            if dataPath not in curList:
                redundList.append(dataPath)
        redundList = list(set(redundList))
        return redundList

    def _import_db_data(self, changedList):
        try:
            for dataPath in changedList:
                coll = self._get_coll_name(dataPath)
                print('import %s...' % dataPath)
                db_coll = self.db[coll]
                readStr = self._read_data_file(dataPath)
                data = yaml.load(readStr)
                data['path'] = dataPath
                data['mtime'] = self._get_modify_time(dataPath)
                db_coll.insert(data)
                db_coll.create_index('tag')
                db_coll.create_index('que')
            print('\n All Complete!')
        except Exception as e:
            print(e)
            print('\n Import Failed!')
