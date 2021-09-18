import json
import requests
from util import getHumanReadTime
import telebot

bot = telebot.TeleBot("1918070708:AAFr3e_yUdqDajNMSLdl6pmBmRhCmcvobxQ")


class NotifyService(object):

    def __init__(self, WxPushUid, TgPushUid = ''):
        self.WxPushUid = WxPushUid
        self.TgPushUid = TgPushUid

    def sendMessageToWX(self, message):
        data = {
            "appToken": "AT_U950xOUDtPQmzFNzOLwI99TaDGPvS7rp",
            "content": message,
            "contentType": 1,  # 内容类型 1表示文字  2表示html(只发送body标签内部的数据即可，不包括body标签) 3表示markdown
            "topicIds": [  # 发送目标的topicId，是一个数组！！！
                123
            ],
            "uids": [self.WxPushUid]
        }
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        requests.post('http://wxpusher.zjiecode.com/api/send/message', data=json.dumps(data), headers=headers)

    def sendMessageToTG(self, message):
        if self.TgPushUid != '' and self.TgPushUid is not None:
            bot.send_message(self.TgPushUid, message)

    def sendMessage(self, message):
        self.sendMessageToWX(message)
        self.sendMessageToTG(message)

    def notify(self, message):
        self.sendMessage('版本更新时间: ' + '2021.07.29 20:00' + '\n时间: ' + getHumanReadTime() + '\n' + message)
