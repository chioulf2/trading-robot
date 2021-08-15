"""
30分钟布林线量化交易模板
1. 做多：
    前两次收盘价格 > MA20，当前MA20 > 前一次MA20
2. 做空：
    前两次收盘价格 < MA20，当前MA20 < 前一次MA20
平多时，开空；平空时，开多。
开仓时间在当前k线结束的时候
"""

import time
from config import globalVar
from util import getMA, getHumanReadTime
from common import batchDoSimpleLong, batchDoSimpleShort
from method import kline, clearPosition

try:
    import thread
except ImportError:
    import _thread as thread


def canDoLong(data):
    MA20 = getMA(data, 20)
    preMA20 = getMA(data, 20, -1)
    pre2MA20 = getMA(data, 20, -2)
    if data[-3][4] > pre2MA20 and data[-2][4] > preMA20 and MA20 > preMA20:
        return True
    return False


def canDoShort(data):
    MA20 = getMA(data, 20)
    preMA20 = getMA(data, 20, -1)
    pre2MA20 = getMA(data, 20, -2)
    if data[-3][4] < pre2MA20 and data[-2][4] < preMA20 and MA20 < preMA20:
        return True
    return False


class Strategy5(object):

    def __init__(self):
        self.users = []
        # 获取历史k线数据，接下来的k线数据在webSocket中更新
        self.kline30m = globalVar['defaultUser'].api.getKline(globalVar['symbol'], '30m')
        self.kline1h = globalVar['defaultUser'].api.getKline(globalVar['symbol'], '1h')
        kline(self, '30m')
        kline(self, '1h')

    def add(self, user):
        clearPosition(user)
        self.users.append(user)

    def remove(self, api_key):
        for i in range(len(self.users)):
            if self.users[i].api_key == api_key:
                clearPosition(self.users[i])
                del self.users[i]
                break

    def sendMsg(self, msg):
        if msg == '':
            return
        for user in self.users:
            user.notifier.notify(msg)

    def sendMsgWhenNoPosition(self, msg):
        if msg == '':
            return
        for user in self.users:
            if not user.position:
                user.notifier.notify(msg)

    def doLong(self):
        batchDoSimpleLong(self.users, globalVar['symbol'])

    def doShort(self):
        batchDoSimpleShort(self.users, globalVar['symbol'])

    def clearPosition(self, p):
        for user in self.users:
            if user.position == p and round((time.time() - user.last_time) / 15 * 60, 2) > 1:
                user.api.deleteAllOrder(globalVar['symbol'])
                user.api.deleteAllPosition(globalVar['symbol'])
                user.position = None
                user.last_time = time.time()
                user.balance = user.getBalance()
                profit = user.balance - user.last_balance
                user.last_balance = user.balance
                if profit < 0:
                    user.loss_count += 1
                else:
                    user.profit_count += 1
                msg = '\n'.join(
                    ['盈利次数: ' + str(user.profit_count) + ' 次',
                     '亏损次数: ' + str(user.loss_count) + ' 次',
                     '总运行时长: ' + str(round((time.time() - globalVar['init_time']) / 3600, 2)) + ' 小时',
                     '总盈亏: ' + str(user.balance - user.init_balance) + ' U',
                     '本次开仓时长: ' + str(round((time.time() - user.last_time) / 3600, 2)) + ' 小时',
                     '本单盈亏: ' + str(profit) + ' U',
                     '平仓时间: ' + getHumanReadTime(),
                     '模式: ' + '一键平仓'])
                user.notifier.notify(msg)

    def strategy(self):
        data = self.kline30m
        if canDoLong(data):
            self.clearPosition('short')
            self.doLong()
        elif canDoShort(data):
            self.clearPosition('long')
            self.doShort()
