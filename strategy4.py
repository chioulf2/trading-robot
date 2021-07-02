# 这个策略是根据15分钟价格偏离MA30的程度来做多做空

from util import *
from common import *

try:
    import thread
except ImportError:
    import _thread as thread


def dealMsg(message):
    if message['e'] == "ORDER_TRADE_UPDATE" and message['o']['x'] == "TRADE" and message['o']['X'] == "FILLED" and \
            (message['o']['ot'] == "STOP_MARKET" or message['o']['ot'] == "LIMIT"):
        def run():
            try:
                orderId = globalVar['orderMap'][message['o']['i']]
                deleteOrder(symbol, orderId)
                globalVar['orderMap'].pop(orderId)
            except Exception as e:
                print(e)
            globalVar['orderMap'].pop(message['o']['i'])
            if message['o']['ot'] == "STOP_MARKET" or message['o']['ot'] == "LIMIT":
                if message['o']['ot'] == "STOP_MARKET":
                    globalVar['loss_count'] += 1
                elif message['o']['ot'] == "LIMIT":
                    globalVar['profit_count'] += 1
                msg = '\n'.join(
                    ['盈利次数: ' + str(globalVar['profit_count']) + ' 次',
                     '亏损次数: ' + str(globalVar['loss_count']) + ' 次',
                     '总运行时长: ' + str(round((time.time() - init_time) / 3600, 2)) + ' 小时',
                     '总盈亏: ' + str(globalVar['balance'] - globalVar['init_balance']) + ' U',
                     '本次开仓时长: ' + str(round((time.time() - globalVar['this_time']) / 3600, 2)) + ' 小时',
                     '本单盈亏: ' + str(message['o']['rp']) + ' U'])
                globalVar['this_time'] = time.time()
                globalVar['piece'] += 1
                print(msg)
                notifyService = NotifyService(msg)
                notifyService.sendMessageToWeiXin()

        thread.start_new_thread(run, ())
    elif message['e'] == "ACCOUNT_UPDATE":
        globalVar['balance'] = float(message['a']['B'][0]['wb'])


def hasTrend(data):
    [MB, UP, LB, PB, BW] = getBoll(data)
    currentPrice = float(data[-1][4])
    if (currentPrice > UP or currentPrice < LB) and abs(currentPrice - MB) / MB > 0.02:
        if currentPrice > UP and abs(currentPrice - UP) / UP > 0.003:
            return 'up'
        if currentPrice < LB and abs(currentPrice - LB) / LB > 0.003:
            return 'down'
    return ''


def trendOver(data):
    MA30 = getMA(data, 30)
    # 上一根K线的收盘价
    currentPrice = float(data[-2][4])
    if currentPrice > MA30 and (currentPrice - MA30) / MA30 > 0.005 or currentPrice < MA30 and (
            MA30 - currentPrice) / MA30 > 0.005:
        return True
    return False


def isNearBollUpOrLb(data):
    [MB, UP, LB, PB, BW] = getBoll(data)
    currentPrice = float(data[-1][4])
    if LB < currentPrice < UP and (UP - LB) / MB > 0.03:
        if currentPrice < MB and abs(currentPrice - LB) / LB < 0.002:
            return 'up'
        if currentPrice > MB and abs(currentPrice - UP) / UP < 0.002:
            return 'down'
    return ''


def loop():
    def run():
        while True:
            data = getKline(symbol, interval)
            # 持仓状态情况下，判断是否应该平仓
            if globalVar['piece'] == 0:
                # 趋势单是否平仓
                closeTrendPosition = globalVar['mode'] == 'trend' and trendOver(data)
                # 震荡单多单是否平仓
                closeShockUpPosition = globalVar['mode'] == 'shockUp' and (
                        hasTrend(data) != '' or isNearBollUpOrLb(data) == 'down')
                # 震荡单空单是否平仓
                closeShockDownPosition = globalVar['mode'] == 'shockDown' and (
                        hasTrend(data) != '' or isNearBollUpOrLb(data) == 'up')
                if closeTrendPosition or closeShockUpPosition or closeShockDownPosition:
                    deleteAllOrder(symbol)
                    deleteAllPosition(symbol)
                    globalVar['piece'] += 1
            # 空仓状态情况下，判断趋势，并判断是否开仓
            else:
                res = hasTrend(data)
                if res == 'up' or res == 'down':
                    globalVar['mode'] = 'trend'
                    if res == 'up':
                        long(symbol, '0.02', 0.1, 0.01)
                    elif res == 'down':
                        short(symbol, '0.02', 0.1, 0.01)
                else:
                    res = isNearBollUpOrLb(data)
                    if res == 'up' or res == 'down':
                        if res == 'up':
                            globalVar['mode'] = 'shockUp'
                            long(symbol, '0.02', 0.05, 0.01)
                        elif res == 'down':
                            globalVar['mode'] = 'shockDown'
                            short(symbol, '0.02', 0.05, 0.01)
            time.sleep(5 * 60)

    thread.start_new_thread(run, ())
