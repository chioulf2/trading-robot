"""
这个策略是通过把市场建模成：趋势行情和震荡行情来实现的，整个策略只需要用到布林线
趋势行情下：追涨杀跌；震荡行情下：高抛低吸
趋势行情：价格突破布林线上下轨0.6%，且开口系数小于3.5%，及时追入，在价格转向后破中轨平仓，或者盈利2%平仓
震荡行情：趋势行情结束后就会进入震荡行情，震荡行情在上下轨内0.2%开仓平仓，或者盈利1%平仓。开口小于2%时不开仓，但可以平仓。

优化：
1. 采样频率设置为：1分钟一次
2. 针市中布林线标准差设置为3
"""

import time
from config import globalVar
from util import getBoll, getMA, getHumanReadTime, isNeedle, isBigNeedle
from common import batchDoShort, batchDoLong
from method import kline, clearPosition

try:
    import thread
except ImportError:
    import _thread as thread


def isNeedleMarketStart(data):
    # 检测一天内的插针的情况 96 = 24*4
    bigNeedleCount = 0
    needleCount = 0
    for i in range(-1, -96):
        if isBigNeedle(data[i]):
            bigNeedleCount += 1
            needleCount += 1
        elif isNeedle(data[i]):
            needleCount += 1
    if bigNeedleCount >= 2 or needleCount >= 6:
        return True
    return False


def isNeedleMarketEnd(data):
    # 检测一天内的插针的情况 96 = 24*4
    bigNeedleCount = 0
    needleCount = 0
    for i in range(-1, -96):
        if isBigNeedle(data[i]):
            bigNeedleCount += 1
            needleCount += 1
        elif isNeedle(data[i]):
            needleCount += 1
    if bigNeedleCount == 0 or needleCount <= 1:
        return True
    return False


class Strategy4(object):

    def __init__(self):
        self.users = []
        # 模式: 分为 "trendOver（趋势结束）", "trendUp(趋势上涨)", "trendDown(趋势下跌)", "shockUp(震荡上涨)", "shockDown(震荡下跌)"
        self.mode = 'trendOver'
        self.isNeedleMarket = False  # 是否是针市
        self.BBandsK = 2  # 多少倍标准差
        self.klineTime = time.time()
        # 获取历史k线数据，接下来的k线数据在webSocket中更新
        self.kline15m = globalVar['defaultUser'].api.getKline(globalVar['symbol'], '15m')
        kline(self, '15m')

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

    def doLong(self, take_profit_scope, stop_scope):
        batchDoLong(self.users, globalVar['symbol'], take_profit_scope, stop_scope)

    def doShort(self, take_profit_scope, stop_scope):
        batchDoShort(self.users, globalVar['symbol'], take_profit_scope, stop_scope)

    def trendOver(self, data):
        msg = ''
        status = False
        MA20 = getMA(data, 20)
        currentPrice = float(data[-1][4])
        if (self.mode == 'trendDown' and currentPrice > MA20 and (
                currentPrice - MA20) / MA20 > 0.004) or (self.mode == 'trendUp' and currentPrice < MA20 and (
                MA20 - currentPrice) / MA20 > 0.004):
            if currentPrice > MA20:
                msg = '下跌趋势结束 当前价格: ' + str(currentPrice) + ' MA20: ' + str(MA20)
            else:
                msg = '上涨趋势结束 当前价格: ' + str(currentPrice) + ' MA20: ' + str(MA20)
            status = True
        return {'status': status, 'msg': msg}

    def shock(self, data):
        msg = ''
        status = ''
        [MB, UP, LB, PB, BW] = getBoll(data, 0, self.BBandsK)
        currentPrice = float(data[-1][4])
        canOpen = (UP - LB) / MB > 0.01
        if LB < currentPrice < UP:
            if currentPrice < MB and currentPrice < LB * (1 + 0.002):
                if canOpen:
                    msg = '震荡开单做多 当前价格: ' + str(currentPrice) + ' 上轨: ' + str(UP) + ' 中轨: ' + str(MB) + ' 下轨: ' + str(
                        LB)
                status = 'LB'
            if currentPrice > MB and currentPrice > UP * (1 - 0.002):
                if canOpen:
                    msg = '震荡开单做空 当前价格: ' + str(currentPrice) + ' 上轨: ' + str(UP) + ' 中轨: ' + str(MB) + ' 下轨: ' + str(
                        LB)
                status = 'UP'
        return {'status': status, 'msg': msg, 'canOpen': canOpen}

    def trend(self, data):
        msg = ''
        status = ''
        [MB, UP, LB, PB, BW] = getBoll(data, 0, self.BBandsK)
        [preMB, preUP, preLB, prePB, preBW] = getBoll(data, -1, self.BBandsK)
        currentPrice = float(data[-1][4])
        if (currentPrice > UP or currentPrice < LB) and preBW < BW < 0.03 and BW > 0.01:
            if currentPrice > UP and abs(currentPrice - UP) / UP > 0.005:
                msg = '趋势开多 当前价格: ' + str(currentPrice) + ' 上轨: ' + str(UP) + ' 中轨: ' + str(MB) + ' 下轨: ' + str(LB)
                status = 'up'
            if currentPrice < LB and abs(currentPrice - LB) / LB > 0.005:
                msg = '趋势开空 当前价格: ' + str(currentPrice) + ' 上轨: ' + str(UP) + ' 中轨: ' + str(MB) + ' 下轨: ' + str(LB)
                status = 'down'
        return {'status': status, 'msg': msg}

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

    def strategy(self):
        if (time.time() - self.klineTime) / 60 < 1:
            return
        self.klineTime = time.time()
        data = self.kline15m
        if not self.isNeedleMarket:
            if not isNeedleMarketStart(data):
                # 继续非针市
                self.DFA(data)
            else:
                # 开始针市
                self.isNeedleMarket = True
                self.sendMsg('开始针市')
                self.BBandsK = 3
                self.DFA(data)
        else:
            if isNeedleMarketEnd(data):
                # 结束针市
                self.isNeedleMarket = False
                self.sendMsg('结束针市')
                self.BBandsK = 2
                self.DFA(data)
            else:
                # 继续针市
                self.DFA(data)

    def judgeTrend(self, data):
        t = self.trend(data)
        if t['status'] == 'up':
            # 单边向上行情，平空，开多
            self.mode = 'trendUp'
            self.clearPosition('short')
            self.sendMsgWhenNoPosition(t['msg'])
            self.doLong(0.02, 0.01)
        elif t['status'] == 'down':
            # 单边向下行情，平多，开空
            self.mode = 'trendDown'
            self.clearPosition('long')
            self.sendMsgWhenNoPosition(t['msg'])
            self.doShort(0.02, 0.01)

    def judgeTrendOver(self, data):
        tOver = self.trendOver(data)
        if tOver['status'] and self.mode == 'trendUp':
            # 单边向上行情结束，平多
            self.mode = 'trendOver'
            self.clearPosition('long')
            self.sendMsg(tOver['msg'])
        elif tOver['status'] and self.mode == 'trendDown':
            # 单边向下行情结束，平空
            self.mode = 'trendOver'
            self.clearPosition('short')
            self.sendMsg(tOver['msg'])

    def judgeShock(self, data):
        # 震荡行情
        s = self.shock(data)
        if s['status'] == 'UP':
            # 震荡到上轨附近，平多，开空
            self.mode = 'shockDown'
            self.clearPosition('long')
            if s['canOpen']:
                self.sendMsgWhenNoPosition(s['msg'])
                self.doShort(0.01, 0.01)
        elif s['status'] == 'LB':
            # 震荡到上轨附近，平空，开多
            self.mode = 'shockUp'
            self.clearPosition('short')
            if s['canOpen']:
                self.sendMsgWhenNoPosition(s['msg'])
                self.doLong(0.01, 0.01)

    def DFA(self, data):
        self.judgeTrend(data)
        if self.mode in ['trendUp', 'trendDown']:
            self.judgeTrendOver(data)
        elif self.mode in ['shockUp', 'shockDown', 'trendOver']:
            self.judgeShock(data)
