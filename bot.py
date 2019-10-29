#!/usr/bin/python3
# -*- coding: utf-8 -*-
from __future__ import print_function

from telegram.ext import Updater
from telegram.ext import CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import common
from common import Prototype

HELP_TEXT = """
Commands
  [/help]                  - show this description.        
  [/check]                 - bot alive check.        
  [/disk]                  - show disk check button.
  [/localdisk]             - show localdisk df -h.
"""


class Bot(Prototype):
    """Telegram API 통신을 해주는 봇으로 채팅방에 접속하여 /start 입력 또는 start 버튼을 클릭하면 활성화 된다."""
    def initialize(self):
        self.grpc_address = f"{self.config['server']['ipaddr']}:{self.config['server']['port']}"
        self.updater = Updater(token=self.config['bot']['token'], use_context=True)
        self.dispatcher = self.updater.dispatcher
        self.add_handler()

    def add_handler(self):
        self.dispatcher.add_handler(CommandHandler('help', self._help))
        self.dispatcher.add_handler(CommandHandler('check', self._bot_check))
        self.dispatcher.add_handler(CommandHandler('disk', self._display_disk_check_menu))
        self.dispatcher.add_handler(CommandHandler('localdisk', self._disk_status))
        self.dispatcher.add_handler(CallbackQueryHandler(self._button))
        self.dispatcher.add_error_handler(self.error)

    def error(self, update, context):
        """Log Errors caused by Updates."""
        self.logger.warning('Update "%s" caused error "%s"', update, context.error)

    def run(self):
        self.logger.info('Telegram receive Bot start...')
        self.updater.start_polling()    # Bot start.
        self.updater.idle()             # 사용자가 Ctrl-C를 누르거나 프로세스가 SIGINT를 받을 때까지 봇을 실행한다.

    def stop(self):
        self.updater.stop()
        self.updater.is_idle = False

    def _help(self, update, context):
        context.bot.send_message(chat_id=update.message.chat_id, text=f'{HELP_TEXT}')

    def _bot_check(self, update, context):
        self.logger.debug('Bot check call....')
        context.bot.send_message(chat_id=update.message.chat_id, text="Bot is alive...")

    def _disk_status(self, update, context):
        self.logger.debug('disk_status call...')
        ipaddr = self.config['target_server']['localhost']['ipaddr']
        text = common.get_cmd_request(self.config, 'disk', 'localhost')
        self.logger.debug(f'RETURN [{text}]')
        context.bot.send_message(chat_id=update.message.chat_id, text=text[ipaddr])

    def _display_disk_check_menu(self, update, context):
        menu_options = [[InlineKeyboardButton(text='Local Disk', callback_data='localhost')]]
        reply_markup = InlineKeyboardMarkup(menu_options)
        update.message.reply_text(text='Select server.', reply_markup=reply_markup)

    def _button(self, update, context):
        query = update.callback_query
        self.logger.debug(query.data)
        select = query.data
        ipaddr = self.config['target_server'][select]['ipaddr']
        if 'localhost' == select:
            text = common.get_cmd_request(self.config, 'disk', select)
        else:
            text = 'Not found option...'
        self.logger.debug(f'{text}')
        query.edit_message_text(text=text[ipaddr])

