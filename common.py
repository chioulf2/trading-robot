from util import getHumanReadTime
import time


def simpleLong(user, symbol, quantity):
    if user.position:
        return
    user.position = 'long'
    user.last_open_time = time.time()
    user.api.level(symbol, user.leverage)
    longOrderId = user.api.order(symbol, 'BUY', 'LONG', 'MARKET', quantity, '')['orderId']
    price = user.api.getOrderPrice(symbol, longOrderId)
    msg = '做多 ' + symbol + ' 量：' + quantity + ' 均价：' + price + ' 时间：' + getHumanReadTime()
    user.notifier.notify(msg)


def simpleShort(user, symbol, quantity):
    if user.position:
        return
    user.position = 'short'
    user.last_open_time = time.time()
    user.api.level(symbol, user.leverage)
    shortOrderId = user.api.order(symbol, 'SELL', 'SHORT', 'MARKET', quantity, '')['orderId']
    price = user.api.getOrderPrice(symbol, shortOrderId)
    msg = '做空 ' + symbol + ' 量：' + quantity + ' 均价：' + price + ' 时间：' + getHumanReadTime()
    user.notifier.notify(msg)


def long(user, symbol, quantity, take_profit_scope, stop_scope):
    if user.position:
        return
    user.position = 'long'
    user.last_open_time = time.time()
    user.api.level(symbol, user.leverage)
    longOrderId = user.api.order(symbol, 'BUY', 'LONG', 'MARKET', quantity, '')['orderId']
    price = user.api.getOrderPrice(symbol, longOrderId)
    try:
        # 止损
        stop_price = str(round(float(price) * (1 - stop_scope), 2))
        res = user.api.order(symbol, 'SELL', 'LONG', 'STOP_MARKET', quantity, '', stop_price)
        stop_orderId = res['orderId']
        status = res['status']
        if status == 'NEW':
            # 止盈
            take_profit_price = str(round(float(price) * (1 + take_profit_scope), 2))
            # take_profit_orderId = order(symbol, 'SELL', 'LONG', 'TRAILING_STOP_MARKET', quantity, '', '', take_profit_price,
            #                             '1.5')
            take_profit_orderId = user.api.order(symbol, 'SELL', 'LONG', 'LIMIT', quantity, take_profit_price)['orderId']
            user.orderMap[take_profit_orderId] = stop_orderId
            user.orderMap[stop_orderId] = take_profit_orderId
    except Exception as e:
        print(e)
    msg = '做多 ' + symbol + ' 量：' + quantity + ' 均价：' + price + ' 时间：' + getHumanReadTime()
    user.notifier.notify(msg)


def short(user, symbol, quantity, take_profit_scope, stop_scope):
    if user.position:
        return
    user.position = 'short'
    user.last_open_time = time.time()
    user.api.level(symbol, user.leverage)
    shortOrderId = user.api.order(symbol, 'SELL', 'SHORT', 'MARKET', quantity, '')['orderId']
    price = user.api.getOrderPrice(symbol, shortOrderId)
    try:
        # 止损
        stop_price = str(round(float(price) * (1 + stop_scope), 2))
        res = user.api.order(symbol, 'BUY', 'SHORT', 'STOP_MARKET', quantity, '', stop_price)
        stop_orderId = res['orderId']
        status = res['status']
        if status == 'NEW':
            # 止盈
            take_profit_price = str(round(float(price) * (1 - take_profit_scope), 2))
            # take_profit_orderId = order(symbol, 'BUY', 'SHORT', 'TRAILING_STOP_MARKET', quantity, '', '', take_profit_price,
            #                             '1.5')
            take_profit_orderId = user.api.order(symbol, 'BUY', 'SHORT', 'LIMIT', quantity, take_profit_price)['orderId']
            user.orderMap[take_profit_orderId] = stop_orderId
            user.orderMap[stop_orderId] = take_profit_orderId
    except Exception as e:
        print(e)
    msg = '做空 ' + symbol + ' 量：' + quantity + ' 均价：' + price + ' 时间：' + getHumanReadTime()
    user.notifier.notify(msg)


def batchDoLong(users, symbol, take_profit_scope, stop_scope):
    for user in users:
        long(user, symbol, user.quantity, take_profit_scope, stop_scope)


def batchDoShort(users, symbol, take_profit_scope, stop_scope):
    for user in users:
        short(user, symbol, user.quantity, take_profit_scope, stop_scope)


def batchDoSimpleLong(users, symbol):
    for user in users:
        simpleLong(user, symbol, user.quantity)


def batchDoSimpleShort(users, symbol):
    for user in users:
        simpleShort(user, symbol, user.quantity)
