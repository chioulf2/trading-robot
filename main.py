#!/usr/bin/env python3
# coding=utf-8
import time
from webSocketListener import WebSocketListener
from user import User
from strategy4 import Strategy4
from strategy5 import Strategy5
from config import globalVar
from messageQueue import MessageQueue
from method import addUser

try:
    import thread
except ImportError:
    import _thread as thread


def main():
    strategy4 = Strategy4()
    strategy5 = Strategy5()
    webSocketPool = []
    for u in globalVar['userConfig']:
        if u[6] == '4':
            addUser(strategy4, webSocketPool, u)
        elif u[6] == '5':
            addUser(strategy5, webSocketPool, u)
    # MessageQueue(strategy)
    while True:
        time.sleep(3600)
        print('主线程 心跳')


main()
