#!/usr/bin/env python3
# coding=utf-8
from webSocketListener import WebSocketListener
from user import User
from strategy4 import Strategy
from config import globalVar
from messageQueue import MessageQueue
from method import addUser

try:
    import thread
except ImportError:
    import _thread as thread


def main():
    strategy = Strategy()
    webSocketPool = []
    for u in globalVar['userConfig']:
        addUser(strategy, webSocketPool, u)
    # MessageQueue(strategy)
    # 获取历史k线数据
    data = globalVar['defaultUser'].api.getKline(globalVar['symbol'], globalVar['interval'])
    globalVar['kline'] = data
    # 接下来的k线数据在webSocket中更新
    kline = globalVar['symbol'].lower() + '@kline_' + '15m'
    listener = WebSocketListener(None, kline, strategy)
    listener.listen()


main()
