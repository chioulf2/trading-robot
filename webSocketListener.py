import websocket
import time
import json
from util import getHumanReadTime, updateKline
from config import globalVar

try:
    import thread
except ImportError:
    import _thread as thread


class WebSocketListener(object):

    def __init__(self, user=None, interval=None, strategy=None):
        self.user = user
        self.interval = interval
        self.listenTime = time.time()
        self.streamName = None
        if interval is not None:
            self.streamName = globalVar['symbol'].lower() + '@kline_' + interval
        self.strategy = strategy
        self.ws = None

    def handleClosePosition(self, message):
        self.user.notifier.notify(json.dumps(message))
        if message['o']['x'] == "TRADE" and (
                message['o']['X'] == "FILLED" or message['o']['X'] == "PARTIALLY_FILLED") and \
                (message['o']['ot'] == "STOP_MARKET" or message['o']['ot'] == "TRAILING_STOP_MARKET" or
                 message['o'][
                     'ot'] == "LIMIT"):
            if message['o']['q'] == message['o']['z']:
                try:
                    orderId = self.user.orderMap[message['o']['i']]
                    self.user.api.deleteOrder(globalVar['symbol'], orderId)
                    self.user.orderMap.pop(orderId)
                    self.user.orderMap.pop(message['o']['i'])
                except Exception as e:
                    print(e)
                    self.user.notifier.notify(str(e))
                try:
                    if message['o']['ot'] == "STOP_MARKET":
                        self.user.loss_count += 1
                    elif message['o']['ot'] == "LIMIT" or message['o']['ot'] == "TRAILING_STOP_MARKET":
                        self.user.profit_count += 1
                    msg = '\n'.join(
                        ['盈利次数: ' + str(self.user.profit_count) + ' 次',
                         '亏损次数: ' + str(self.user.loss_count) + ' 次',
                         '总运行时长: ' + str(round((time.time() - globalVar['init_time']) / 3600, 2)) + ' 小时',
                         '总盈亏: ' + str(self.user.balance - self.user.init_balance) + ' U',
                         '本次开仓时长: ' + str(round((time.time() - self.user.last_open_time) / 3600, 2)) + ' 小时',
                         '本单盈亏: ' + str(message['o']['rp']) + ' U',
                         '平仓时间: ' + getHumanReadTime(),
                         '模式: ' + '止盈止损'])
                    self.user.position = None
                    self.user.last_close_time = time.time()
                    self.user.last_balance = self.user.getBalance()
                    self.user.notifier.notify(msg)
                except Exception as e:
                    self.user.notifier.notify(str(e))
            else:
                self.user.notifier.notify('部分成交，总成交量:' + message['o']['q'] + ' 累计成交量:' + message['o']['z'])

    def on_message(self, ws, message):
        message = json.loads(message)
        message = message['data']
        if message['e'] == "listenKeyExpired":
            print('listenKey过期 ', getHumanReadTime())
            ws.close()
            self.listenStreams()
        elif message['e'] == 'ACCOUNT_UPDATE':
            self.user.balance = float(message['a']['B'][0]['wb'])
        elif message['e'] == "ORDER_TRADE_UPDATE":
            self.handleClosePosition(message)
        elif message['e'] == "kline":
            # 大于23小时重连（每24小时服务器会断开连接）
            if (time.time() - self.listenTime) / 3600 > 23:
                ws.close()
                self.listenStreams()
                return
            self.strategy.kline = updateKline(self.strategy.kline, message)
            if self.strategy is not None:
                self.strategy.strategy()

    def on_error(self, ws, error):
        print(ws)
        print(error)

    def on_close(self, ws):
        print("### 关闭WebSocket ###")
        print(ws)

    def on_open(self, ws):
        print("### 开启WebSocket ###")
        print(ws)

    def listenStreams(self):
        print('before 监听WebSocket')
        if self.streamName:
            streamNames = '/'.join([self.streamName])
            self.listenTime = time.time()
        else:
            streamNames = '/'.join([self.user.api.getListenKey()])
        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp("wss://fstream.binance.com/stream?streams=" + streamNames,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_open=self.on_open,
                                         on_close=self.on_close)
        print('after 监听WebSocket')
        self.ws.run_forever(sslopt={"check_hostname": False})

    def listenOnThread(self):
        def run():
            self.listenStreams()

        thread.start_new_thread(run, ())

    def listen(self):
        self.listenStreams()

    def close(self):
        self.ws.close()
