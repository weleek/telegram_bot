#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
from urllib import parse
from threading import Thread

from processors import Worker, WorkerProcess, Message
import common


class ProducerProcess(Worker):
    """작업을 배당하기 위한 선행으로 SSH 접속하여 정보를 읽어오는 역할"""
    def __init__(self, core):
        super().__init__()
        self.core = core
        self.default_polling_interval = int(self.config['polling_time']['disk_interval'])
        self.logger.info(f'{self.__class__.__name__} initialize call..')

    def polling(self):
        if self.core.analysis is not None:
            outputs = {}
            self.logger.info('GET DISK SPACE INFORMATION START...')
            threads = [Thread(target=common.get_disk_space(i, output=outputs)) for i in self.config['target_server'].values()]
            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()
            self.logger.info('GET DISK SPACE INFORMATION END...')
            self.core.analysis.add(Message('DISK', obj=outputs))
            pass


class AnalysisProcess(WorkerProcess):
    """전달 받은 메세지를 분류 하는 역할"""
    def __init__(self, core):
        super().__init__()
        self.core = core
        self.default_polling_interval = int(self.config['polling_time']['disk_interval'])
        self.URL = f'https://api.telegram.org/bot{self.config["bot"]["token"]}/sendMessage?chat_id={self.config["bot"]["chat_id"]}&text='
        self.logger.info(f'{self.__class__.__name__} initialize call...')

    def on_action(self, job_type, information):
        if job_type == 'DISK':
            self.send_messages(information)
        pass

    def send_message(self, text):
        self.logger.info(text)
        os.system(f'curl -X GET "{self.URL}{parse.quote(text)}"')

    def send_messages(self, obj):
        self.logger.info(obj)
        for k, v in obj.items():
            if v != "":
                text = f"{k} \n{v}"
                os.system(f'curl -X GET "{self.URL}{parse.quote(text)}"')

