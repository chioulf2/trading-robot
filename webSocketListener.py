import websocket
import time
import json
from util import getHumanReadTime
from config import symbol, init_time, globalVar

try:
    import thread
except ImportError:
    import _thread as thread


class WebSocketListener(object):

    def __init__(self, user, streamName, strategy=None):
        self.user = user
        self.streamName = streamName
        self.strategy = strategy

    def listenStreams(self):
        def handleClosePosition(message):
            if message['o']['x'] == "TRADE" and (
                    message['o']['X'] == "FILLED" or message['o']['X'] == "PARTIALLY_FILLED") and \
                    (message['o']['ot'] == "STOP_MARKET" or message['o']['ot'] == "TRAILING_STOP_MARKET" or
                     message['o'][
                         'ot'] == "LIMIT"):
                def run():
                    try:
                        orderId = self.user.orderMap[message['o']['i']]
                        self.user.api.deleteOrder(symbol, orderId)
                        self.user.orderMap.pop(orderId)
                        self.user.orderMap.pop(message['o']['i'])
                    except Exception as e:
                        print(e)
                    if message['o']['ot'] == "STOP_MARKET":
                        self.user.loss_count += 1
                    elif message['o']['ot'] == "LIMIT" or message['o']['ot'] == "TRAILING_STOP_MARKET":
                        self.user.profit_count += 1
                    msg = '\n'.join(
                        ['盈利次数: ' + str(self.user.profit_count) + ' 次',
                         '亏损次数: ' + str(self.user.loss_count) + ' 次',
                         '总运行时长: ' + str(round((time.time() - init_time) / 3600, 2)) + ' 小时',
                         '总盈亏: ' + str(self.user.balance - self.user.init_balance) + ' U',
                         '本次开仓时长: ' + str(round((time.time() - self.user.last_time) / 3600, 2)) + ' 小时',
                         '本单盈亏: ' + str(message['o']['rp']) + ' U',
                         '平仓时间: ' + getHumanReadTime(),
                         '模式: ' + '止盈止损'])
                    self.user.last_time = time.time()
                    self.user.position = False
                    self.user.notifier.sendMessageToWeiXin(msg)

                thread.start_new_thread(run, ())

        def on_message(ws, message):
            message = json.loads(message)
            message = message['data']
            if message['e'] == "listenKeyExpired":
                print('listenKey过期 ', getHumanReadTime())
                ws.close()
                self.listenStreams()
            elif message['e'] == 'ACCOUNT_UPDATE':
                self.user.balance = float(message['a']['B'][0]['wb'])
            elif message['e'] == "ORDER_TRADE_UPDATE":
                handleClosePosition(message)
            elif message['e'] == "kline":
                newItem = [message['k']['t'], message['k']['o'], message['k']['h'], message['k']['l'],
                           message['k']['c'],
                           message['k']['v'], message['k']['T'], message['k']['q'], message['k']['n'],
                           message['k']['V'],
                           message['k']['Q'], message['k']['B']]
                if globalVar['kline'][-1][0] != message['k']['t']:
                    globalVar['kline'].append(newItem)
                    del globalVar['kline'][0]
                else:
                    globalVar['kline'][-1] = newItem
                if self.strategy is not None:
                    self.strategy.strategy()

        def on_error(ws, error):
            print(ws)
            print(error)

        def on_close(ws):
            print("### 关闭WebSocket ###")
            print(ws)
            self.listenStreams()

        def on_open(ws):
            print("### 开启WebSocket ###")
            print(ws)
            pass

        streamNames = '/'.join([self.streamName])
        websocket.enableTrace(True)
        ws = websocket.WebSocketApp("wss://fstream.binance.com/stream?streams=" + streamNames,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_open=on_open,
                                    on_close=on_close)
        print('重启WebSocket')
        ws.run_forever(sslopt={"check_hostname": False})

    def listenOnThread(self):
        def run():
            self.listenStreams()

        thread.start_new_thread(run, ())

    def listen(self):
        self.listenStreams()
