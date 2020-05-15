import sys
import yadisk
import json
import os.path
import posixpath
import os
from logger import get_logger
import logging

logger = get_logger('disk')
logger.setLevel(logging.INFO)


class Disk:
    def __init__(self):
        self.api = None
        if not os.path.isfile('config.json'):
            print('Перейдите по адресу https://oauth.yandex.ru/client/new и создайте приложение с правами Яндекс.Диск REST API')
            self.APPLICATION_ID = input('Введите  ID приложения: ')
            self.APPLICATION_SECRET = input('Введите пароль приложения: ')
            self.PATH = input('Введите путь к локальной папке синхронизации (/<имя_папки>): ')
            self.REMOTE_PATH = input('Введите путь к папке синхронизации на Яндекс-диске (/<имя_папки>): ')
            config = {
                'APPLICATION_ID': self.APPLICATION_ID,
                'APPLICATION_SECRET': self.APPLICATION_SECRET,
                'PATH': self.PATH,
                'REMOTE_PATH': self.REMOTE_PATH
            }
            with open('config.json', 'w') as json_file:
                json.dump(config, json_file)
        with open('config.json') as json_file:
            config = json.load(json_file)
            self.APPLICATION_ID = config.get('APPLICATION_ID')
            self.APPLICATION_SECRET = config.get('APPLICATION_SECRET')
            self.PATH = config.get('PATH')
            self.REMOTE_PATH = config.get('REMOTE_PATH')
            self.TOKEN = config.get('TOKEN')

    def save(self):
        config = {
            'APPLICATION_ID': self.APPLICATION_ID,
            'APPLICATION_SECRET': self.APPLICATION_SECRET,
            'PATH': self.PATH,
            'REMOTE_PATH': self.REMOTE_PATH,
            'TOKEN': self.TOKEN
        }
        with open('config.json', 'w') as json_file:
            json.dump(config, json_file)

    def get_assets(self):
        self.api = yadisk.YaDisk(token=self.TOKEN)
        if self.api.check_token():
            logger.info('Диск подключен по текущему токену')
            return self.api

        self.api = yadisk.YaDisk(self.APPLICATION_ID, self.APPLICATION_SECRET)
        url = self.api.get_code_url()

        logger.info(f'Перейдите по ссылке: {url}')
        code = input("Введите код: ")

        try:
            response = self.api.get_token(code)
        except yadisk.exceptions.BadRequestError:
            logger.error("Bad code")
            sys.exit(1)

        self.api.token = response.access_token
        self.TOKEN = self.api.token
        self.save()
        logger.info(f'Получен новый токен: {self.TOKEN}')

        if self.api.check_token():
            logger.info(f'Диск подключен')
        else:
            logger.error("Что-то пошло не так... Диск не подключен")

    def recursive_upload(self):
        if not self.api:
            logger.error('Диск не подключен')
            return None

        files_count = 0
        this_file = 0
        progress_step = 0

        logger.info(f'Подготовка к копированию...')
        for root, dirs, files in os.walk(self.PATH):
            files_count += len(files)

        for root, dirs, files in os.walk(self.PATH):
            p = root.split(self.PATH)[1].strip(os.path.sep)
            dir_path = posixpath.join(self.REMOTE_PATH, p)

            try:
                self.api.mkdir(dir_path)
            except yadisk.exceptions.PathExistsError:
                pass

            for file in files:
                file_path = posixpath.join(dir_path, file)
                p_sys = p.replace("/", os.path.sep)
                in_path = os.path.join(self.PATH, p_sys, file)
                try:
                    this_file += 1
                    progress = int(this_file / files_count * 100)
                    logger.debug(f'Загрузка файла {file} ({this_file} из {files_count}) {progress}%')
                    if progress >= progress_step:
                        logger.info(f'Копирование файлов {progress}%...')
                        progress_step += 10
                    self.api.upload(in_path, file_path)
                except yadisk.exceptions.PathExistsError:
                    logger.debug(f'Файл {file} уже существует в папке назначния. Пропуск...')
                    pass