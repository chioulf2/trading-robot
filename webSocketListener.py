import hmac
import hashlib
import websocket
import requests
from config import *
from strategy4 import strategy, handleClosePosition

try:
    import thread
except ImportError:
    import _thread as thread


def on_message(ws, message):
    message = json.loads(message)
    print(message)
    if message['e'] == "listenKeyExpired":
        print('listenKey过期')
        ws.close()
        listenStreams()
    elif message['e'] == 'ACCOUNT_UPDATE':
        globalVar['balance'] = float(message['a']['B'][0]['wb'])
    elif message['e'] == "ORDER_TRADE_UPDATE":
        handleClosePosition(message)
    elif message['e'] == "kline":
        newItem = [message['k']['t'], message['k']['o'], message['k']['h'], message['k']['l'], message['k']['c'],
                   message['k']['v'], message['k']['T'], message['k']['q'], message['k']['n'], message['k']['V'],
                   message['k']['Q'], message['k']['B']]
        if globalVar['kline'][-1][0] != message['k']['t']:
            globalVar['kline'].append(newItem)
        else:
            globalVar['kline'][-1] = newItem
        strategy()


def on_error(ws, error):
    print(ws)
    print(error)


def on_close(ws):
    print("### 关闭WebSocket ###")
    listenStreams()


def on_open(ws):
    pass


def getListenKey():
    method = '/fapi/v1/listenKey'
    signature = hmac.new(bytes(secret_key, 'utf-8'), msg=bytes('', 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    response = requests.post(
        'https://' + host + method + '?signature=' + signature,
        headers=headers)
    content = json.loads(response.content)
    print('获取listenKey')
    return content['listenKey']


def listen(streamName):
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://fstream.binance.com/ws/" + streamName,
                                on_message=on_message,
                                on_error=on_error,
                                on_open=on_open,
                                on_close=on_close)
    print('重启WebSocket')
    ws.run_forever(sslopt={"check_hostname": False})


def listenStreams():
    listenKey = getListenKey()
    kline = symbol.lower() + '@kline_' + '15m'

    def run():
        listen(kline)

    thread.start_new_thread(run, ())
    listen(listenKey)
