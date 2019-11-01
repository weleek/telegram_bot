# -*- coding: utf-8 -*-
import os
import multiprocessing
import threading
import queue
from common import (logger_init, AESCipher, print_exception)
from abc import ABCMeta, abstractmethod
import yaml

WORK_DIR = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/'))


class Message(metaclass=ABCMeta):
    """interface 역할"""
    @abstractmethod
    def process(self, worker):
        pass


class SendQuit(Message):
    """모든 프로세스에게 프로세스 종료를 하기 위한 클래스"""
    def process(self, worker):
        worker.do_quit()


class Message(Message):
    """기본 사전형 자료구조를 전파하기 위한 원형 클래스"""
    def __init__(self, job_type, obj=dict()):
        self.job_type = job_type
        self.information = obj
        pass

    def process(self, worker):
        worker.on_action(self.job_type, self.information)
        pass


class Prototype:
    """공통 로거 모듈 정의 및 설정 모듈을 초기화 하기 위해 원형 클래스 생성"""
    def __init__(self, process_name=None):
        self.process_name = self.__class__.__name__ if process_name is None else process_name
        with open(f"{WORK_DIR}/config.yaml", 'r') as stream:
            config = yaml.safe_load(stream)
        self.config = config
        self.config['bot']['token'] = AESCipher('1029384756123456').decrypt(self.config['bot']['token'])
        self.logger = logger_init(self.process_name, config['logging']['level'].upper())


class Worker(Prototype):
    def __init__(self):
        self.name = self.__class__.__name__
        super().__init__(self.name)
        self.quit = False
        self.queue = multiprocessing.Queue()
        self.sleep_event = threading.Event()
        self.default_polling_interval = 1
        self.thread = None

    def add(self, message):
        self.queue.put(message)

    def wait(self, t):
        self.sleep_event.wait(t)

    def stop(self):
        self.quit = True
        self.sleep_event.set()
        self.queue.put(SendQuit())

    def run(self):
        t = threading.Thread(target=self.process, name=self.name, args=())
        self.thread = t
        t.daemon = True
        t.start()

    def polling(self):
        pass

    def do_quit(self):
        self.quit = True

    def process(self):
        while not self.quit:
            #self.polling()
            try:
                self.polling()
                found = self.queue.get(True, self.default_polling_interval)
                found.process(self)
            except queue.Empty:
                found = None
            except KeyboardInterrupt:
                found = None
                self.quit = True
            except Exception as e:
                print_exception()


class WorkerProcess(Prototype):
    def __init__(self):
        self.name = self.__class__.__name__
        super().__init__(self.name)
        self.quit = False
        self.queue = multiprocessing.Queue()
        self.sleep_event = threading.Event()
        self.default_polling_interval = 1

    def add(self, message):
        self.queue.put(message)

    def wait(self, t):
        self.sleep_event.wait(t)

    def join(self):
        assert (self.process is not None)
        self.process.join()

    def do_quit(self):
        self.quit = True

    def stop(self):
        self.quit = True
        self.sleep_event.set()
        self.queue.put(SendQuit())
        # self.process.kill()

    def run(self):
        t = multiprocessing.Process(target=self.process, name=self.name, args=())
        self.process = t
        t.start()

    def polling(self):
        pass

    def process(self):
        while not self.quit:
            #self.polling()
            try:
                self.polling()
                found = self.queue.get(True, self.default_polling_interval)
                found.process(self)
            except queue.Empty:
                found = None
            except KeyboardInterrupt:
                fount = None
                self.quit = True
            except Exception as e:
                print_exception()
