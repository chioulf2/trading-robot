from user import User
from webSocketListener import WebSocketListener
from config import globalVar


def clearPosition(user):
    user.api.deleteAllOrder(globalVar['symbol'])
    user.api.deleteAllPosition(globalVar['symbol'])


def addUser(strategy, webSocketPool, u):
    if u['active'] == 'false':
        return
    user = User(u, globalVar['proxies'])
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


def kline(strategy, interval):
    listener = WebSocketListener(None, interval, strategy)
    listener.listenOnThread()

