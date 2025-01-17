"""
这个策略是通过把市场建模成：趋势行情和震荡行情来实现的，整个策略只需要用到布林线
趋势行情下：追涨杀跌；震荡行情下：高抛低吸
趋势行情：价格突破布林线上下轨0.5%，且开口系数小于3%，及时追入，在价格转向后破中轨平仓，或者盈利2%平仓
震荡行情：趋势行情结束后就会进入震荡行情，震荡行情在上下轨内0.2%开仓平仓，或者盈利1%平仓。开口小于2%时不开仓，但可以平仓。

优化：
1. 采样频率设置为：5秒一次
2. 针市中布林线标准差设置为3
3. 采用4个k线，以15分钟线为基础，如果1h,4h,1d有一个跟15分钟线趋势相同，则可以开单，否则不可以，且根据模式匹配的数量决定止盈幅度
4. 中轨斜率过大，比如5根k线斜率大于0.0013，就进入趋势行情
5. 弥补漏洞：trendOver要平掉所有仓位

15分钟参数:
趋势行情：开口系数小于3%，价格突破布林线上下轨0.5%

一小时参数:
趋势行情：开口系数小于5%，价格突破布林线上下轨0.9%

4小时参数:
趋势行情：开口系数小于9.5%，价格突破布林线上下轨1.6%

日线参数:
趋势行情：开口系数小于16.3%，价格突破布林线上下轨4.1%

改动：
之前没有对历史模式进行判断，导致self.mode一开始默认为trendOver，现在增加了对历史模式进行判断
开仓是有时效性的，只有状态转变的时候才可以开仓，所以需要记录最近一次状态改变的时间，如果当前时间跟上次状态改变的时间很接近则可以开仓
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

params = {
    '15m': {
        'BW': 0.025,
        'break': 0.005
    },
    '1h': {
        'BW': 0.052,
        'break': 0.009,
    },
    '4h': {
        'BW': 0.095,
        'break': 0.016,
    },
    '1d': {
        'BW': 0.163,
        'break': 0.041,
    }
}

# 止损幅度
stopScope = 0.003
profitScope = {
    '3': 0.005,
    '2': 0.005,
    '1': 0.005,
    '0': 0.005
}


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


class Mode(object):

    def __init__(self, interval, manager):
        self.updateTime = time.time()
        self.manager = manager
        self.scope = 0.003
        self.stopScope = 0.003
        self.canOpen = True
        self.msg = ''
        self.oldMsg = ''
        self.interval = interval
        # 模式: 分为 "trendOver（趋势结束）", "trendUp(趋势上涨)", "trendDown(趋势下跌)", "shockUp(震荡上涨)", "shockDown(震荡下跌)"
        self.mode = 'trendOver'
        self.oldMode = self.mode
        self.changeModeTime = 0  # 模式改变的时间
        self.isNeedleMarket = False  # 是否是针市
        self.BBandsK = 2  # 多少倍标准差
        self.prepare()
        # 获取历史k线数据，接下来的k线数据在webSocket中更新
        self.kline = globalVar['defaultUser'].api.getKline(globalVar['symbol'], interval)
        kline(self, interval)

    def prepare(self):
        """
        在开始之前，先对历史状态进行一个模式识别，即设置self.mode
        :return:
        """
        kline = globalVar['defaultUser'].api.getKline(globalVar['symbol'], self.interval, 400)
        for i in range(200):
            self.kline = kline[i:i + 200]
            self.strategy(False)

    def strategy(self, sideEffect=True):
        # if (time.time() - self.klineTime) / 60 < 1:
        #     return
        # self.klineTime = time.time()
        data = self.kline
        if not self.isNeedleMarket:
            if not isNeedleMarketStart(data):
                # 继续非针市
                self.DFA(data)
            else:
                # 开始针市
                self.isNeedleMarket = True
                self.BBandsK = 3
                self.DFA(data)
        else:
            if isNeedleMarketEnd(data):
                # 结束针市
                self.isNeedleMarket = False
                self.BBandsK = 2
                self.DFA(data)
            else:
                # 继续针市
                self.DFA(data)
        if sideEffect:
            if self.interval == '15m' and time.time() - self.updateTime > 5 and abs(
                    float(data[-1][2]) - float(data[-1][3])) / float(
                    data[-1][1]) < 0.015:
                self.updateTime = time.time()
                self.manager.strategy()

    def DFA(self, data):
        self.judgeTrend(data)
        if self.mode in ['trendUp', 'trendDown']:
            self.judgeTrendOver(data)
        elif self.mode in ['shockUp', 'shockDown', 'trendOver']:
            self.judgeShock(data)

    def judgeTrend(self, data):
        t = self.trend(data)
        if t['status'] == 'up':
            # 单边向上行情，平空，开多
            self.mode = 'trendUp'
            if self.oldMode != self.mode:
                self.oldMode = self.mode
                self.changeModeTime = data[-1][0] / 1000
                self.oldMsg = self.msg
        elif t['status'] == 'down':
            # 单边向下行情，平多，开空
            self.mode = 'trendDown'
            if self.oldMode != self.mode:
                self.oldMode = self.mode
                self.changeModeTime = data[-1][0] / 1000
                self.oldMsg = self.msg

    def judgeTrendOver(self, data):
        tOver = self.trendOver(data)
        if tOver['status'] and self.mode == 'trendUp':
            # 单边向上行情结束，平多
            self.mode = 'trendOver'
            if self.oldMode != self.mode:
                self.oldMode = self.mode
                self.changeModeTime = data[-1][0] / 1000
                self.oldMsg = self.msg
        elif tOver['status'] and self.mode == 'trendDown':
            # 单边向下行情结束，平空
            self.mode = 'trendOver'
            if self.oldMode != self.mode:
                self.oldMode = self.mode
                self.changeModeTime = data[-1][0] / 1000
                self.oldMsg = self.msg

    def judgeShock(self, data):
        # 震荡行情
        s = self.shock(data)
        if s['status'] == 'UP':
            # 震荡到上轨附近，平多，开空
            self.mode = 'shockDown'
            if self.oldMode != self.mode:
                self.oldMode = self.mode
                self.changeModeTime = data[-1][0] / 1000
                self.oldMsg = self.msg
        elif s['status'] == 'LB':
            # 震荡到上轨附近，平空，开多
            self.mode = 'shockUp'
            if self.oldMode != self.mode:
                self.oldMode = self.mode
                self.changeModeTime = data[-1][0] / 1000
                self.oldMsg = self.msg

    def trendOver(self, data):
        status = False
        MA20 = getMA(data, 20)
        currentPrice = float(data[-1][4])
        high = float(data[-1][2])
        low = float(data[-1][3])
        if (self.mode == 'trendDown' and currentPrice > MA20 and (
                currentPrice - MA20) / MA20 > 0.004) or (self.mode == 'trendUp' and currentPrice < MA20 and (
                MA20 - currentPrice) / MA20 > 0.004):
            if currentPrice > MA20:
                self.msg = '下跌趋势结束 当前价格: ' + str(currentPrice) + ' MA20: ' + str(MA20)
            else:
                self.msg = '上涨趋势结束 当前价格: ' + str(currentPrice) + ' MA20: ' + str(MA20)
            status = True
        return {'status': status}

    def shock(self, data):
        status = ''
        [MB, UP, LB, PB, BW] = getBoll(data, 0, self.BBandsK)
        [preMB, preUP, preLB, prePB, preBW] = getBoll(data, -1, self.BBandsK)
        [pre5MB, pre5UP, pre5LB, pre5PB, pre5BW] = getBoll(data, -5, self.BBandsK)
        if abs(pre5MB - MB) / min(pre5MB, MB) > 0.001:
            return {'status': status}
        currentPrice = float(data[-1][4])
        high = float(data[-1][2])
        low = float(data[-1][3])
        # self.canOpen = (UP - LB) / MB > 0.01
        if LB < currentPrice < UP:
            if currentPrice < MB and low < LB * (1 + (BW / 10)):
                if self.canOpen:
                    self.msg = '震荡开单做多 当前价格: ' + str(currentPrice) + ' 上轨: ' + str(UP) + ' 中轨: ' + str(
                        MB) + ' 下轨: ' + str(
                        LB)
                status = 'LB'
                self.scope = 0.003
                if self.scope > BW * 0.7:
                    self.scope = BW * 0.7
            if currentPrice > MB and high > UP * (1 - (BW / 10)):
                if self.canOpen:
                    self.msg = '震荡开单做空 当前价格: ' + str(currentPrice) + ' 上轨: ' + str(UP) + ' 中轨: ' + str(
                        MB) + ' 下轨: ' + str(
                        LB)
                status = 'UP'
                self.scope = 0.003
                if self.scope > BW * 0.7:
                    self.scope = BW * 0.7
        return {'status': status}

    def trend(self, data):
        status = ''
        [MB, UP, LB, PB, BW] = getBoll(data, 0, self.BBandsK)
        [preMB, preUP, preLB, prePB, preBW] = getBoll(data, -1, self.BBandsK)
        [pre10MB, pre10UP, pre10LB, pre10PB, pre10BW] = getBoll(data, -10, self.BBandsK)
        if abs(pre10MB - MB) / min(pre10MB, MB) > 0.001:
            return {'status': status}
        currentPrice = float(data[-1][4])
        high = float(data[-1][2])
        low = float(data[-1][3])
        if (currentPrice > UP or currentPrice < LB) and preBW < BW < params[self.interval]['BW']:
            if currentPrice > UP and abs(high - UP) / UP > params[self.interval]['break']:
                self.msg = '趋势开多 当前价格: ' + str(currentPrice) + ' 上轨: ' + str(UP) + ' 中轨: ' + str(MB) + ' 下轨: ' + str(LB)
                status = 'up'
            if currentPrice < LB and abs(low - LB) / LB > params[self.interval]['break']:
                self.msg = '趋势开空 当前价格: ' + str(currentPrice) + ' 上轨: ' + str(UP) + ' 中轨: ' + str(MB) + ' 下轨: ' + str(LB)
                status = 'down'
        return {'status': status}


class Strategy4(object):

    def __init__(self):
        self.users = []
        self.mode15m = None
        self.mode1d = None
        self.mode4h = None
        self.mode1h = None
        self.mode15m = Mode('15m', self)
        self.mode1d = Mode('1d', self)
        self.mode4h = Mode('4h', self)
        self.mode1h = Mode('1h', self)
        self.oldChangeModeTime = 0  # 上次模式改变的时间，如果和本次模式改变时间相同，则不开仓
        self.oldMode = ''
        pass

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

    def upAndDownCount(self):
        up = 0
        down = 0
        if self.mode1h.mode in ['trendUp', 'shockUp']:
            up = up + 1
        elif self.mode1h.mode in ['trendDown', 'shockDown']:
            down = down + 1
        if self.mode4h.mode in ['trendUp', 'shockUp']:
            up = up + 1
        elif self.mode4h.mode in ['trendDown', 'shockDown']:
            down = down + 1
        if self.mode1d.mode in ['trendUp', 'shockUp']:
            up = up + 1
        elif self.mode1d.mode in ['trendDown', 'shockDown']:
            down = down + 1
        return {'up': up, 'down': down}

    def getScore(self):
        score = 0
        if self.mode1d.mode == 'trendUp':
            score = score + 1
        elif self.mode1d.mode == 'trendDown':
            score = score - 1
        if self.mode4h.mode == 'trendUp':
            score = score + 1
        elif self.mode4h.mode == 'trendDown':
            score = score - 1
        if self.mode1h.mode == 'trendUp':
            score = score + 1
        elif self.mode1h.mode == 'trendDown':
            score = score - 1
        if self.mode15m.mode == 'trendDown':
            score = -score
        if score < 0:
            score = 0
        return str(score)

    def setScope(self):
        if self.mode15m.mode in ['trendDown', 'trendUp']:
            # res = self.upAndDownCount()
            # if res['up'] == 3 or res['down'] == 3:
            #     self.mode15m.scope = 0.05
            # elif res['up'] == 2 or res['down'] == 2:
            #     self.mode15m.scope = 0.02
            # elif res['up'] == 1 or res['down'] == 1:
            #     self.mode15m.scope = 0.005
            pass
            score = self.getScore()
            print('当前打分: ', score)
            if score in profitScope:
                self.mode15m.scope = profitScope[score]
            self.mode15m.stopScope = 0.005

    def strategy(self):
        # 等待初始化完成
        if not self.mode15m or not self.mode1d or not self.mode4h or not self.mode1h:
            return

        # 打印必要信息
        print('\n\n\n')
        print('当前时间: ' + getHumanReadTime())
        print('模式改变时间：' + getHumanReadTime(self.mode15m.changeModeTime))
        print('模式改变详情: ' + self.mode15m.oldMsg)
        print('目前的模式：15分钟模式: ', self.mode15m.mode, ', 一小时模式: ', self.mode1h.mode,
              ', 四小时模式: ',
              self.mode4h.mode, ', 一天模式: ', self.mode1d.mode, '\n')

        # 必须在模式改变的这跟k线开仓，保证时效性
        if time.time() - self.mode15m.changeModeTime > 15 * 60:
            return
        # 通过新旧对比来判断15分钟模式是否改变
        if self.oldChangeModeTime == self.mode15m.changeModeTime and self.oldMode == self.mode15m.mode:
            return
        self.oldMode = self.mode15m.mode
        # 设置时间让下一单无法开出
        self.oldChangeModeTime = self.mode15m.changeModeTime
        self.setScope()
        if self.mode15m.mode == 'trendUp' or self.mode15m.mode == 'shockUp':
            self.clearPosition('short')
            if self.mode15m.canOpen:
                self.doLong(self.mode15m.scope, stopScope)
        elif self.mode15m.mode == 'trendDown' or self.mode15m.mode == 'shockDown':
            self.clearPosition('long')
            if self.mode15m.canOpen:
                self.doShort(self.mode15m.scope, stopScope)
