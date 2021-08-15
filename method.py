from user import User
from webSocketListener import WebSocketListener
from config import globalVar


def addUser(strategy, webSocketPool, u):
    if u[-1] == 'true':
        return
    user = User(*u[:6])
    strategy.add(user)
    listener = WebSocketListener(user, None)
    listener.listenOnThread()
    webSocketPool.append(listener)


def removeUser(strategy, webSocketPool, api_key):
    strategy.remove(api_key)
    for i in range(len(webSocketPool)):
        if webSocketPool[i].api_key == api_key:
            del webSocketPool[i]
            break


def kline15m(strategy):
    # 获取历史k线数据
    data = globalVar['defaultUser'].api.getKline(globalVar['symbol'], '15m')
    globalVar['kline15m'] = data
    # 接下来的k线数据在webSocket中更新
    kline = globalVar['symbol'].lower() + '@kline_' + '15m'
    listener = WebSocketListener(None, kline, strategy)
    listener.listenOnThread()


def kline30m(strategy):
    # 获取历史k线数据
    data = globalVar['defaultUser'].api.getKline(globalVar['symbol'], '30m')
    globalVar['kline30m'] = data
    # 接下来的k线数据在webSocket中更新
    kline = globalVar['symbol'].lower() + '@kline_' + '30m'
    listener = WebSocketListener(None, kline, strategy)
    listener.listenOnThread()
