from user import User
from webSocketListener import WebSocketListener


def addUser(strategy, u):
    if u[7] == 'true':
        return
    user = User(*u[:5])
    strategy.add(user)
    listener = WebSocketListener(user, None)
    listener.listenOnThread()
