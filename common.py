# -*- coding: utf-8 -*-
import os
import sys
import logging
import colorlog
from pexpect import pxssh
from pathlib import Path
import linecache
import traceback
import base64
from Crypto.Cipher import AES
from Crypto import Random

WORK_DIR = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/'))


class AESCipher:
    def __init__(self, key):
        self.key = key
        BS = 16
        self.pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
        self.unpad = lambda s: s[:-ord(s[len(s) - 1:])]

    def encrypt(self, raw):
        raw = self.pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw)).decode()

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:16]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self.unpad(cipher.decrypt(enc[16:])).decode()


def logger_init(module_name='', level='INFO', logger=None):
    logger = logging.getLogger(module_name) if logger is None else logger
    logger.setLevel(level)
    fmt = '%(log_color)s%(levelname)6s %(asctime)s %(name)16s(%(lineno)4s) %(threadName)16s - %(message)s'
    formatter = colorlog.ColoredFormatter(fmt)
    handler = colorlog.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def print_exception():
    exc_type, exc_obj, tb = sys.exc_info()
    stk = traceback.extract_tb(tb, 1)
    f = tb.tb_frame
    lineno = tb.tb_lineno
    funcname = stk[0][2]
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print(f'\x1b[1;37;41m[EXCEPTION]\x1b[0m {exc_type.__name__}: Message "{exc_obj}", File "{filename}", Line {lineno}, in {funcname}\n\t{line.strip()}')


def _get_client(options):
    if options['password'] == '' and options['keyfile'] == '':
        raise Exception('need ssh-keyfile path.')
    ssh = pxssh.pxssh(timeout=60, encoding='utf-8')
    ssh.login(options['ipaddr'], options['username'], password=options['password'] if options['password'] else '',
              port=options['port'] or None,
              ssh_key=options['keyfile'].replace('~/', f'{str(Path.home())}/') if options['keyfile'] else None)
    return ssh


def get_disk_space(options, output={}):
    ssh = _get_client(options)
    ssh.sendline(f'df -h')
    ssh.prompt()
    output[options['ipaddr']] = ssh.before.strip().replace('\r', '')
    ssh.logout()
    ssh.close()

