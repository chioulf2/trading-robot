from binanceApi import *
from notify import *


def long(symbol, quantity, take_profit_scope, stop_scope):
    if globalVar['position']:
        return
    globalVar['position'] = True
    level(symbol, leverage)
    longOrderId = order(symbol, 'BUY', 'LONG', 'MARKET', quantity, '')['orderId']
    price = getOrderPrice(symbol, longOrderId)
    try:
        # 止损
        stop_price = str(round(float(price) * (1 - stop_scope), 2))
        res = order(symbol, 'SELL', 'LONG', 'STOP_MARKET', quantity, '', stop_price)
        stop_orderId = res['orderId']
        status = res['status']
        if status == 'NEW':
            # 止盈
            take_profit_price = str(round(float(price) * (1 + take_profit_scope), 2))
            take_profit_orderId = order(symbol, 'SELL', 'LONG', 'TRAILING_STOP_MARKET', quantity, '', '', take_profit_price,
                                        '1.5')
            # take_profit_orderId = order(symbol, 'SELL', 'LONG', 'LIMIT', quantity, take_profit_price)['orderId']
            globalVar['orderMap'][take_profit_orderId] = stop_orderId
            globalVar['orderMap'][stop_orderId] = take_profit_orderId
    except Exception as e:
        print(e)
    msg = '做多 ' + symbol + ' 量：' + quantity + ' 均价：' + price + ' 时间：' + getHumanReadTime()
    print(msg)
    notifyService = NotifyService(msg)
    notifyService.sendMessageToWeiXin()


def short(symbol, quantity, take_profit_scope, stop_scope):
    if globalVar['position']:
        return
    globalVar['position'] = True
    level(symbol, leverage)
    shortOrderId = order(symbol, 'SELL', 'SHORT', 'MARKET', quantity, '')['orderId']
    price = getOrderPrice(symbol, shortOrderId)
    try:
        # 止损
        stop_price = str(round(float(price) * (1 + stop_scope), 2))
        res = order(symbol, 'BUY', 'SHORT', 'STOP_MARKET', quantity, '', stop_price)
        stop_orderId = res['orderId']
        status = res['status']
        if status == 'NEW':
            # 止盈
            take_profit_price = str(round(float(price) * (1 - take_profit_scope), 2))
            take_profit_orderId = order(symbol, 'BUY', 'SHORT', 'TRAILING_STOP_MARKET', quantity, '', '', take_profit_price,
                                        '1')
            # take_profit_orderId = order(symbol, 'BUY', 'SHORT', 'LIMIT', quantity, take_profit_price)['orderId']
            globalVar['orderMap'][take_profit_orderId] = stop_orderId
            globalVar['orderMap'][stop_orderId] = take_profit_orderId
    except Exception as e:
        print(e)
    msg = '做空 ' + symbol + ' 量：' + quantity + ' 均价：' + price + ' 时间：' + getHumanReadTime()
    print(msg)
    notifyService = NotifyService(msg)
    notifyService.sendMessageToWeiXin()
