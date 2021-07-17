#!/usr/bin/env python3
# coding=utf-8
from webSocketListener import WebSocketListener
from user import User
from strategy4 import Strategy
from config import globalVar, symbol, interval

try:
    import thread
except ImportError:
    import _thread as thread


def main():
    strategy = Strategy()
    # 接下来的k线数据在webSocket中更新
    for u in globalVar['userConfig']:
        user = User(*u[:3])
        strategy.add(user)
        listener = WebSocketListener(user, user.listenKey)
        listener.listenOnThread()
    # 获取历史k线数据
    data = globalVar['defaultUser'].getKline(symbol, interval)
    globalVar['kline'] = data
    kline = symbol.lower() + '@kline_' + '15m'
    listener = WebSocketListener(globalVar['defaultUser'], kline, strategy)
    listener.listen()


main()
