# 这个策略是根据15分钟价格偏离MA30的程度来做多做空

import time
from config import symbol, quantity, globalVar, init_time
from util import getBoll, getMA, getHumanReadTime
from common import batchDoShort, batchDoLong

try:
    import thread
except ImportError:
    import _thread as thread


class Strategy(object):

    def __init__(self):
        self.users = []

    def add(self, user):
        self.users.append(user)

    def doLong(self):
        batchDoLong(self.users, symbol, quantity, 0.02, 0.01)

    def doShort(self):
        batchDoShort(self.users, symbol, quantity, 0.02, 0.01)

    def trend(self, data):
        [MB, UP, LB, PB, BW] = getBoll(data)
        [preMB, preUP, preLB, prePB, preBW] = getBoll(data, -1)
        currentPrice = float(data[-1][4])
        if (currentPrice > UP or currentPrice < LB) and preBW < BW < 0.035:
            if currentPrice > UP and abs(currentPrice - UP) / UP > 0.006:
                for user in self.users:
                    if not user.position:
                        msg = '趋势开多 当前价格: ' + str(currentPrice) + ' 上轨: ' + str(UP) + ' 中轨: ' + str(MB) + ' 下轨: ' + str(LB)
                        user.notifier.notify(msg)
                return 'up'
            if currentPrice < LB and abs(currentPrice - LB) / LB > 0.006:
                for user in self.users:
                    if not user.position:
                        msg = '趋势开空 当前价格: ' + str(currentPrice) + ' 上轨: ' + str(UP) + ' 中轨: ' + str(MB) + ' 下轨: ' + str(LB)
                        user.notifier.notify(msg)
                return 'down'
        return ''

    def trendOver(self, data):
        MA20 = getMA(data, 20)
        currentPrice = float(data[-1][4])
        if (globalVar['mode'] == 'trendDown' and currentPrice > MA20 and (
                currentPrice - MA20) / MA20 > 0.004) or (globalVar['mode'] == 'trendUp' and currentPrice < MA20 and (
                MA20 - currentPrice) / MA20 > 0.004):
            globalVar['mode'] = 'trendOver'
            for user in self.users:
                if currentPrice > MA20:
                    msg = '下跌趋势结束 当前价格: ' + str(currentPrice) + ' MA20: ' + str(MA20)
                else:
                    msg = '上涨趋势结束 当前价格: ' + str(currentPrice) + ' MA20: ' + str(MA20)
                user.notifier.notify(msg)
            return True
        return False

    def shock(self, data):
        [MB, UP, LB, PB, BW] = getBoll(data)
        currentPrice = float(data[-1][4])
        canOpen = (UP - LB) / MB > 0.02
        if LB < currentPrice < UP:
            if currentPrice < MB and currentPrice < LB * (1 + 0.002):
                for user in self.users:
                    if not user.position:
                        msg = '震荡开单做多 当前价格: ' + str(currentPrice) + ' 上轨: ' + str(UP) + ' 中轨: ' + str(MB) + ' 下轨: ' + str(
                            LB)
                        user.notifier.notify(msg)
                return ['LB', canOpen]
            if currentPrice > MB and currentPrice > UP * (1 - 0.002):
                for user in self.users:
                    if not user.position:
                        msg = '震荡开单做空 当前价格: ' + str(currentPrice) + ' 上轨: ' + str(UP) + ' 中轨: ' + str(MB) + ' 下轨: ' + str(
                            LB)
                        user.notifier.notify(msg)
                return ['UP', canOpen]
        return ['', False]

    def clearPosition(self, type):
        for user in self.users:
            if user.position == type and round((time.time() - user.last_time) / 15 * 60, 2) > 1:
                user.position = None
                user.api.deleteAllOrder(symbol)
                user.api.deleteAllPosition(symbol)
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
                     '总运行时长: ' + str(round((time.time() - init_time) / 3600, 2)) + ' 小时',
                     '总盈亏: ' + str(user.balance - user.init_balance) + ' U',
                     '本次开仓时长: ' + str(round((time.time() - user.last_time) / 3600, 2)) + ' 小时',
                     '本单盈亏: ' + str(profit) + ' U',
                     '平仓时间: ' + getHumanReadTime(),
                     '模式: ' + '一键平仓'])
                user.notifier.notify(msg)

    def strategy(self):
        data = globalVar['kline']
        if globalVar['mode'] in ['shockUp', 'shockDown', 'trendOver']:
            [direction, canOpen] = self.shock(data)
            if direction == 'UP':
                globalVar['mode'] = 'shockDown'
                self.clearPosition('long')
            if canOpen:
                self.doShort()
        elif globalVar['mode'] in ['shockUp', 'shockDown', 'trendOver']:
            [direction, canOpen] = self.shock(data)
            if direction == 'LB':
                globalVar['mode'] = 'shockUp'
                self.clearPosition('short')
            if canOpen:
                self.doLong()
        elif globalVar['mode'] == 'trendUp' and self.trendOver(data):
            globalVar['mode'] = 'trendOver'
            self.clearPosition('long')
            self.doLong()
        elif globalVar['mode'] == 'trendDown' and self.trendOver(data):
            globalVar['mode'] = 'trendOver'
            self.clearPosition('short')
            self.doShort()
        elif self.trend(data) == 'up':
            globalVar['mode'] = 'trendUp'
            self.clearPosition('short')
            self.doLong()
        elif self.trend(data) == 'down':
            globalVar['mode'] = 'trendDown'
            self.clearPosition('long')
            self.doShort()
