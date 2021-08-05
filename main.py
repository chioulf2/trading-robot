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
    for u in globalVar['userConfig']:
        user = User(*u[:5])
        strategy.add(user)
        listener = WebSocketListener(user, None)
        listener.listenOnThread()
    # 获取历史k线数据
    data = globalVar['defaultUser'].api.getKline(symbol, interval)
    globalVar['kline'] = data
    # 接下来的k线数据在webSocket中更新
    kline = symbol.lower() + '@kline_' + '15m'
    listener = WebSocketListener(None, kline, strategy)
    listener.listen()


main()
