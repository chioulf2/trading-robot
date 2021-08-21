"""
30分钟布林线量化交易模板
总原则：平多时，开空；平空时，开多。
优先级：趋势 > 趋势前 > 震荡
趋势前：
    1. 做多：
        前两次收盘价格 > MA20，当前MA20 > 前一次MA20，(1小时中轨向下 and 价格 <= MA20) or (时间在当前k线结束的时候)
    2. 做空：
        前两次收盘价格 < MA20，当前MA20 < 前一次MA20，(1小时中轨向上 and 价格 >= MA20) or (时间在当前k线结束的时候)
趋势：
    1. 做多：
        连续两次收盘价大于上轨，立即做多
    2. 做空：
        连续两次收盘价小于下轨，立即做空
震荡：
    趋势和趋势前开仓后进行判断，其中趋势开仓后需要等3个小时才能进行震荡判断
    1. 做多：
        开多后，连续三次收盘价小于上轨，第四次收盘平多转空
    2. 做空：
        开空后，连续三次收盘价大于下轨，第四次收盘平空转多
"""

import time
from config import globalVar
from util import getMA, getHumanReadTime, getBoll
from common import batchDoSimpleLong, batchDoSimpleShort
from method import kline, clearPosition

try:
    import thread
except ImportError:
    import _thread as thread


class Strategy5(object):

    def __init__(self):
        self.users = []
        self.mode = ''
        self.trendBeginTime = 0
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
            if user.position == p and round((time.time() - user.last_open_time) / 15 * 60, 2) > 1:
                user.api.deleteAllOrder(globalVar['symbol'])
                user.api.deleteAllPosition(globalVar['symbol'])
                user.position = None
                user.last_close_time = time.time()
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
                     '本次开仓时长: ' + str(round((time.time() - user.last_open_time) / 3600, 2)) + ' 小时',
                     '本单盈亏: ' + str(profit) + ' U',
                     '平仓时间: ' + getHumanReadTime(),
                     '模式: ' + '一键平仓'])
                user.notifier.notify(msg)

    def preTrend(self):
        MA20 = getMA(self.kline30m, 20)
        preMA20 = getMA(self.kline30m, 20, -1)
        pre2MA20 = getMA(self.kline30m, 20, -2)
        _1hMA20 = getMA(self.kline1h, 20)
        _1hPreMA20 = getMA(self.kline1h, 20, -1)
        currentPrice = float(self.kline30m[-1][4])
        prePrice = float(self.kline30m[-2][4])
        pre2Price = float(self.kline30m[-3][4])
        currentKlineTime = self.kline30m[-1][0] / 1000
        if pre2Price > pre2MA20 and prePrice > preMA20 and MA20 > preMA20 and (
                (_1hMA20 < _1hPreMA20 and currentPrice <= MA20) or
                ((time.time() - currentKlineTime) > 1790)
        ):
            return 'long'
        elif pre2Price < pre2MA20 and prePrice < preMA20 and MA20 < preMA20 and (
                (_1hMA20 > _1hPreMA20 and currentPrice >= MA20) or
                ((time.time() - currentKlineTime) > 1790)
        ):
            return 'short'
        return ''

    def trend(self):
        [preMB, preUP, preLB, prePB, preBW] = getBoll(self.kline30m, -1)
        [pre2MB, pre2UP, pre2LB, pre2PB, pre2BW] = getBoll(self.kline30m, -2)
        prePrice = float(self.kline30m[-2][4])
        pre2Price = float(self.kline30m[-3][4])
        if pre2Price > pre2UP and prePrice > preUP:
            return 'long'
        elif pre2Price < pre2LB and prePrice < preLB:
            return 'short'
        return ''

    def shock(self):
        currentKlineTime = self.kline30m[-1][0] / 1000
        if time.time() - currentKlineTime > 1790:
            [preMB, preUP, preLB, prePB, preBW] = getBoll(self.kline30m, -1)
            [pre2MB, pre2UP, pre2LB, pre2PB, pre2BW] = getBoll(self.kline30m, -2)
            [pre3MB, pre3UP, pre3LB, pre3PB, pre3BW] = getBoll(self.kline30m, -3)
            prePrice = float(self.kline30m[-2][4])
            pre2Price = float(self.kline30m[-3][4])
            pre3Price = float(self.kline30m[-4][4])
            if self.mode in ['preTrendUp',
                             'trendUp'] and pre3Price < pre3UP and pre2Price < pre2UP and prePrice < preUP:
                return 'short'
            elif self.mode in ['preTrendDown',
                               'trendDown'] and pre3Price > pre3UP and pre2Price > pre2UP and prePrice > preUP:
                return 'long'
        return ''

    def strategy(self):
        trend = self.trend()
        if trend == 'long':
            self.mode = 'trendUp'
            self.trendBeginTime = time.time()
            self.clearPosition('short')
            self.doLong()
        elif trend == 'short':
            self.mode = 'trendDown'
            self.trendBeginTime = time.time()
            self.clearPosition('long')
            self.doShort()
        else:
            preTrend = self.preTrend()
            if preTrend == 'long':
                self.mode = 'preTrendUp'
                self.clearPosition('short')
                self.doLong()
            elif preTrend == 'short':
                self.mode = 'preTrendDown'
                self.clearPosition('long')
                self.doShort()
            elif time.time() - self.trendBeginTime > 3600 * 3:
                shock = self.shock()
                if shock == 'long':
                    self.mode = 'shockUp'
                    self.clearPosition('short')
                    self.doLong()
                elif shock == 'short':
                    self.mode = 'shockDown'
                    self.clearPosition('long')
                    self.doShort()
