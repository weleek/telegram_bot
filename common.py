# -*- coding: utf-8 -*-
import os
import ast
import yaml
import grpc
import logging
import colorlog
from pexpect import pxssh
from pathlib import Path
from abc import *

import network_pb2 as desc
import network_pb2_grpc as ngrpc

WORK_DIR = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/'))


class Prototype(metaclass=ABCMeta):
    def __init__(self):
        with open(f"{WORK_DIR}/config.yaml", 'r') as stream:
            config = yaml.safe_load(stream)
        self.config = config
        self.logger = logger_init(self.__class__.__name__, config['logging']['level'].upper())
        self.initialize()

    @abstractmethod
    def initialize(self):
        pass


def logger_init(module_name='', level='INFO', logger=None):
    logger = logging.getLogger(module_name) if logger is None else logger
    logger.setLevel(level)
    fmt = '%(log_color)s%(levelname)6s %(asctime)s %(name)16s(%(lineno)4s) %(threadName)16s - %(message)s'
    formatter = colorlog.ColoredFormatter(fmt)
    handler = colorlog.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def _get_client(options):
    if options['password'] == '' and options['keyfile'] == '':
        raise Exception('need ssh-keyfile path.')
    ssh = pxssh.pxssh(timeout=60, encoding='utf-8')
    ssh.login(options['ipaddr'], options['username'], password=options['password'] if options['password'] else '',
              port=options['port'] or None, ssh_key=options['keyfile'].replace('~/', f'{str(Path.home())}/') if options['keyfile'] else None)
    return ssh


def get_disk_space(options, output={}):
    ssh = _get_client(options)
    ssh.sendline(f'df -h')
    ssh.prompt()
    output[options['ipaddr']] = ssh.before.strip().replace('\r', '')
    ssh.logout()
    return output


def get_cmd_request(config, cmd_type, select, options=''):
    grpc_address = f"{config['server']['ipaddr']}:{config['server']['port']}"
    with grpc.insecure_channel(grpc_address) as channel:
        stub = ngrpc.NetworkStub(channel)
        result = stub.CmdRequest(desc.Request(type=cmd_type, target=select, options=options))
    result = ast.literal_eval(result.json)
    return result

