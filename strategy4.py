# 这个策略是根据15分钟价格偏离MA30的程度来做多做空

from util import *
from common import *

try:
    import thread
except ImportError:
    import _thread as thread


def handleClosePosition(message):
    if message['o']['x'] == "TRADE" and message['o']['X'] == "FILLED" and \
            (message['o']['ot'] == "STOP_MARKET" or message['o']['ot'] == "TRAILING_STOP_MARKET" or message['o'][
                'ot'] == "LIMIT"):
        def run():
            try:
                orderId = globalVar['orderMap'][message['o']['i']]
                deleteOrder(symbol, orderId)
                globalVar['orderMap'].pop(orderId)
            except Exception as e:
                print(e)
            globalVar['orderMap'].pop(message['o']['i'])
            if message['o']['ot'] == "STOP_MARKET":
                globalVar['loss_count'] += 1
            elif message['o']['ot'] == "LIMIT" or message['o']['ot'] == "TRAILING_STOP_MARKET":
                globalVar['profit_count'] += 1
            msg = '\n'.join(
                ['盈利次数: ' + str(globalVar['profit_count']) + ' 次',
                 '亏损次数: ' + str(globalVar['loss_count']) + ' 次',
                 '总运行时长: ' + str(round((time.time() - init_time) / 3600, 2)) + ' 小时',
                 '总盈亏: ' + str(globalVar['balance'] - globalVar['init_balance']) + ' U',
                 '本次开仓时长: ' + str(round((time.time() - globalVar['this_time']) / 3600, 2)) + ' 小时',
                 '本单盈亏: ' + str(message['o']['rp']) + ' U',
                 '平仓时间: ' + getHumanReadTime()])
            globalVar['this_time'] = time.time()
            globalVar['position'] = False
            print(msg)
            notifyService = NotifyService(msg)
            notifyService.sendMessageToWeiXin()

        thread.start_new_thread(run, ())


def hasTrend(data):
    [MB, UP, LB, PB, BW] = getBoll(data)
    [preMB, preUP, preLB, prePB, preBW] = getBoll(data, -1)
    currentPrice = float(data[-1][4])
    if (currentPrice > UP or currentPrice < LB) and 0.035 > abs(UP - LB) / MB > 0.025 and abs(
            preUP - preLB) / preMB < abs(UP - LB) / MB:
        if currentPrice > UP and abs(currentPrice - UP) / UP > 0.004:
            return 'up'
        if currentPrice < LB and abs(currentPrice - LB) / LB > 0.004:
            return 'down'
    return ''


def trendOver(data, type):
    MA30 = getMA(data, 30)
    # 上一根K线的收盘价
    currentPrice = float(data[-2][4])
    if (type == 'trendDown' and currentPrice > MA30 and (
            currentPrice - MA30) / MA30 > 0.003) or (type == 'Up' and currentPrice < MA30 and (
            MA30 - currentPrice) / MA30 > 0.003):
        return True
    return False


def isNearBollUpOrLb(data):
    [MB, UP, LB, PB, BW] = getBoll(data)
    currentPrice = float(data[-1][4])
    if LB < currentPrice < UP and (UP - LB) / MB > 0.03:
        if currentPrice < MB and currentPrice < LB * (1 + 0.002):
            return 'up'
        if currentPrice > MB and currentPrice > UP * (1 - 0.002):
            return 'down'
    return ''


def strategy():
    data = globalVar['kline']
    # 持仓状态情况下，判断是否应该平仓
    if globalVar['position']:
        # 趋势多单是否平仓
        closeTrendUpPosition = globalVar['mode'] == 'trendUp' and trendOver(data, 'trendUp')
        # 趋势空单是否平仓
        closeTrendDownPosition = globalVar['mode'] == 'trendDown' and trendOver(data, 'trendDown')
        if closeTrendUpPosition or closeTrendDownPosition:
            globalVar['mode'] = 'trendOver'
        # 震荡单多单是否平仓
        closeShockUpPosition = globalVar['mode'] == 'shockUp' and (
                hasTrend(data) != '' or isNearBollUpOrLb(data) == 'down')
        # 震荡单空单是否平仓
        closeShockDownPosition = globalVar['mode'] == 'shockDown' and (
                hasTrend(data) != '' or isNearBollUpOrLb(data) == 'up')
        if closeTrendUpPosition or closeTrendDownPosition or closeShockUpPosition or closeShockDownPosition:
            deleteAllOrder(symbol)
            deleteAllPosition(symbol)
            notifyService = NotifyService('一键平仓, 时间:' + getHumanReadTime())
            notifyService.sendMessageToWeiXin()
            globalVar['position'] = False
    # 空仓状态情况下，判断趋势，并判断是否开仓
    elif not globalVar['position']:
        res = hasTrend(data)
        if res == 'up' or res == 'down':
            if res == 'up':
                globalVar['mode'] = 'trendUp'
                long(symbol, quantity, 0.02, 0.01)
            elif res == 'down':
                globalVar['mode'] = 'trendDown'
                short(symbol, quantity, 0.02, 0.01)
        elif globalVar['mode'] == 'trendOver' or globalVar['mode'] == 'shockDown' or \
                globalVar['mode'] == 'shockUp':
            res = isNearBollUpOrLb(data)
            if res == 'up' or res == 'down':
                if res == 'up':
                    globalVar['mode'] = 'shockUp'
                    long(symbol, quantity, 0.02, 0.01)
                elif res == 'down':
                    globalVar['mode'] = 'shockDown'
                    short(symbol, quantity, 0.02, 0.01)
