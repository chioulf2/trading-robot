#!/usr/bin/env python3
# coding=utf-8
# from strategy1 import *
import random
from strategy4 import *
from webSocketListener import *
from util import *


globalVar['init_balance'] = getBalance()  # 初始资产


def main():
    # 获取历史k线数据
    data = getKline(symbol, interval)
    globalVar['kline'] = data
    # 接下来的k线数据在webSocket中更新
    listenStreams()


main()