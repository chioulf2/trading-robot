# 这个策略是根据15分钟价格偏离MA30的程度来做多做空

from util import *
from common import *

try:
    import thread
except ImportError:
    import _thread as thread


def doLong():
    long(symbol, quantity, 0.02, 0.01)


def doShort():
    short(symbol, quantity, 0.02, 0.01)


def handleClosePosition(message):
    if message['o']['x'] == "TRADE" and (message['o']['X'] == "FILLED" or message['o']['X'] == "PARTIALLY_FILLED") and \
            (message['o']['ot'] == "STOP_MARKET" or message['o']['ot'] == "TRAILING_STOP_MARKET" or message['o'][
                'ot'] == "LIMIT"):
        def run():
            try:
                orderId = globalVar['orderMap'][message['o']['i']]
                deleteOrder(symbol, orderId)
                globalVar['orderMap'].pop(orderId)
                globalVar['orderMap'].pop(message['o']['i'])
            except Exception as e:
                print(e)
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
            notify(msg)

        thread.start_new_thread(run, ())


def trend(data):
    [MB, UP, LB, PB, BW] = getBoll(data)
    [preMB, preUP, preLB, prePB, preBW] = getBoll(data, -1)
    currentPrice = float(data[-1][4])
    if (currentPrice > UP or currentPrice < LB) and preBW < BW < 0.035:
        if currentPrice > UP and abs(currentPrice - UP) / UP > 0.006:
            if globalVar['mode'] != 'trendUp':
                clearPosition()
            globalVar['mode'] = 'trendUp'
            if not globalVar['position']:
                doLong()
                msg = '趋势开多 当前价格: ' + str(currentPrice) + ' 上轨: ' + str(UP) + ' 中轨: ' + str(MB) + ' 下轨: ' + str(LB)
                notify(msg)
            return 'up'
        if currentPrice < LB and abs(currentPrice - LB) / LB > 0.006:
            if globalVar['mode'] != 'trendDown':
                clearPosition()
            globalVar['mode'] = 'trendDown'
            if not globalVar['position']:
                doShort()
                msg = '趋势开空 当前价格: ' + str(currentPrice) + ' 上轨: ' + str(UP) + ' 中轨: ' + str(MB) + ' 下轨: ' + str(LB)
                notify(msg)
            return 'down'
    return ''


def trendOver(data):
    MA30 = getMA(data, 30)
    # 上一根K线的收盘价
    currentPrice = float(data[-2][4])
    if (globalVar['mode'] == 'trendDown' and currentPrice > MA30 and (
            currentPrice - MA30) / MA30 > 0.003) or (globalVar['mode'] == 'trendUp' and currentPrice < MA30 and (
            MA30 - currentPrice) / MA30 > 0.003):
        globalVar['mode'] = 'trendOver'
        clearPosition()
        msg = '趋势结束 当前价格: ' + str(currentPrice) + ' MA30: ' + str(MA30)
        notify(msg)
        return True
    return False


def shock(data):
    [MB, UP, LB, PB, BW] = getBoll(data)
    currentPrice = float(data[-1][4])
    if globalVar['mode'] == 'trendOver' and LB < currentPrice < UP and (UP - LB) / MB > 0.02:
        if currentPrice < MB and currentPrice < LB * (1 + 0.002):
            if globalVar['mode'] != 'shockUp':
                clearPosition()
            globalVar['mode'] = 'shockUp'
            if not globalVar['position']:
                doLong()
                msg = '震荡开单做多 当前价格: ' + str(currentPrice) + ' 上轨: ' + str(UP) + ' 中轨: ' + str(MB) + ' 下轨: ' + str(LB)
                notify(msg)
            return 'up'
        if currentPrice > MB and currentPrice > UP * (1 - 0.002):
            if globalVar['mode'] != 'shockDown':
                clearPosition()
            globalVar['mode'] = 'shockDown'
            if not globalVar['position']:
                doShort()
                msg = '震荡开单做空 当前价格: ' + str(currentPrice) + ' 上轨: ' + str(UP) + ' 中轨: ' + str(MB) + ' 下轨: ' + str(LB)
                notify(msg)
            return 'down'
    return ''


def clearPosition():
    if globalVar['position']:
        globalVar['position'] = False
        deleteAllOrder(symbol)
        deleteAllPosition(symbol)
        msg = ' 总盈亏: ' + str(globalVar['balance'] - globalVar['init_balance']) + ' U'
        notify('一键平仓, 时间: ' + getHumanReadTime() + msg)


def strategy():
    data = globalVar['kline']
    trendOver(data)
    shock(data)
    trend(data)
