from user import User
from webSocketListener import WebSocketListener


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

