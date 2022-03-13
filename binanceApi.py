import hmac
import hashlib
import requests
import json
from util import getTime


class BinanceApi(object):

    def __init__(self, api_key, secret_key, proxies):
        self.secret_key = secret_key
        self.host = "fapi.binance.com"
        self.headers = {
            "X-MBX-APIKEY": api_key
        }
        self.proxies = proxies

    def getSignature(self, msg):
        return hmac.new(bytes(self.secret_key, 'utf-8'), msg=bytes(msg, 'utf-8'), digestmod=hashlib.sha256).hexdigest()

    def getRequest(self, method, msg, signature):
        return requests.get(
            'https://' + self.host + method + '?' + msg + '&signature=' + signature,
            headers=self.headers, proxies=self.proxies)

    def postRequest(self, method, msg, signature):
        return requests.post(
            'https://' + self.host + method + '?' + msg + '&signature=' + signature,
            headers=self.headers, proxies=self.proxies)

    def deleteRequest(self, method, msg, signature):
        return requests.delete(
            'https://' + self.host + method + '?' + msg + '&signature=' + signature,
            headers=self.headers, proxies=self.proxies)

    def getBalance(self):
        method = '/fapi/v2/balance'
        timestamp = str(getTime())
        msg = '&'.join(
            ['timestamp=' + timestamp])
        signature = self.getSignature(msg)
        response = self.getRequest(method, msg, signature)
        content = json.loads(response.content)
        # 只统计U本位合约的资产
        u_balance = 0
        for i in range(len(content)):
            if content[i]['asset'] == 'USDT':
                u_balance = content[i]['balance']
        print('资产: ', str(u_balance), ' U')
        return float(u_balance)

    def getUserData(self, symbol):
        method = '/fapi/v2/account'
        timestamp = str(getTime())
        msg = '&'.join(
            ['timestamp=' + timestamp])
        signature = self.getSignature(msg)
        response = self.getRequest(method, msg, signature)
        content = json.loads(response.content)
        long = ''
        short = ''
        for i in range(len(content['positions'])):
            if content['positions'][i]['symbol'] == symbol:
                if content['positions'][i]['positionSide'] == 'LONG':
                    long = content['positions'][i]['positionAmt']
                if content['positions'][i]['positionSide'] == 'SHORT':
                    short = content['positions'][i]['positionAmt']
        return {'long': float(long), 'short': -float(short)}

    def getPrice(self, symbol):
        method = '/fapi/v1/ticker/price'
        timestamp = str(getTime())
        params = ['symbol=' + symbol,
                  'timestamp=' + timestamp]
        msg = '&'.join(params)
        signature = self.getSignature(msg)
        response = self.getRequest(method, msg, signature)
        content = json.loads(response.content)
        print(content)
        return content['price']

    def level(self, symbol, leverage='1'):
        # 币安
        method = '/fapi/v1/leverage'
        timestamp = str(getTime())
        msg = '&'.join(
            ['symbol=' + symbol, 'leverage=' + leverage, 'timestamp=' + timestamp])
        signature = self.getSignature(msg)
        response = self.postRequest(method, msg, signature)
        content = json.loads(response.content)
        print('设置合约倍数为：' + leverage)
        return content

    def getOrderPrice(self, symbol, orderId):
        # 获取已成交订单的成交价格
        method = '/fapi/v1/order'
        orderId = str(orderId)
        timestamp = str(getTime())
        msg = '&'.join(
            ['symbol=' + symbol, 'orderId=' + orderId,
             'timestamp=' + timestamp])
        signature = self.getSignature(msg)
        response = self.getRequest(method, msg, signature)
        content = json.loads(response.content)
        if 'avgPrice' in content:
            price = str(round(float(content['avgPrice']), 2))
            print('成交价: ' + price)
            return price
        return '0.0'

    def order(self, symbol, side, positionSide, type, quantity, price, stopPrice='', activationPrice='',
              callbackRate='5',
              closePosition='false'):
        print('下单')
        print('stopPrice ', stopPrice)
        method = '/fapi/v1/order'
        timestamp = str(getTime())
        params = ['symbol=' + symbol, 'side=' + side, 'type=' + type,
                  'positionSide=' + positionSide,
                  'timestamp=' + timestamp, 'quantity=' + quantity]
        if closePosition == 'true':
            params.pop()
            params.append('closePosition=' + str(closePosition))
        if type == 'LIMIT':
            price = str(round(float(price), 2))
            params.append('price=' + price)
            params.append('timeInForce=' + 'GTC')
        if type == 'STOP_MARKET':
            if stopPrice == '':
                stopPrice = '0'
            stopPrice = str(round(float(stopPrice), 2))
            params.append('stopPrice=' + stopPrice)
        if type == 'TRAILING_STOP_MARKET':
            params.append('activationPrice=' + str(activationPrice))
            params.append('callbackRate=' + str(callbackRate))

        msg = '&'.join(params)
        signature = self.getSignature(msg)
        response = self.postRequest(method, msg, signature)
        content = json.loads(response.content)
        msg = '挂单成功 ' + 'price ' + price + 'stopPrice ' + stopPrice
        print(msg)
        print(content)
        if 'orderId' in content:
            return {'orderId': content['orderId'], 'status': content['status']}
        return {'orderId': 0, 'status': 'FAILED'}

    def deleteAllOrder(self, symbol):
        method = '/fapi/v1/allOpenOrders'
        timestamp = str(getTime())
        msg = '&'.join(
            ['symbol=' + symbol,
             'timestamp=' + timestamp])
        signature = self.getSignature(msg)
        response = self.deleteRequest(method, msg, signature)
        content = json.loads(response.content)
        print('删除所有挂单')
        print(content)

    def deleteAllPosition(self, symbol):
        res = self.getUserData(symbol)
        longQuantity = res['long']
        shortQuantity = res['short']
        if longQuantity > 0:
            self.order(symbol, 'SELL', 'LONG', 'MARKET', str(longQuantity), '')
        if shortQuantity > 0:
            self.order(symbol, 'BUY', 'SHORT', 'MARKET', str(shortQuantity), '')

    def deleteOrder(self, symbol, orderId):
        method = '/fapi/v1/order'
        orderId = str(orderId)
        timestamp = str(getTime())
        msg = '&'.join(
            ['symbol=' + symbol,
             'timestamp=' + timestamp, 'orderId=' + orderId])
        signature = self.getSignature(msg)
        response = self.deleteRequest(method, msg, signature)
        content = json.loads(response.content)
        print('取消挂单: ', orderId)
        print(content)

    def getListenKey(self):
        method = '/fapi/v1/listenKey'
        timestamp = str(getTime())
        msg = '&'.join(
            ['timestamp=' + timestamp])
        signature = self.getSignature(msg)
        response = self.postRequest(method, msg, signature)
        content = json.loads(response.content)
        print('获取listenKey')
        return content['listenKey']

    def getKline(self, symbol, interval, limit=200):
        '''
        :param symbol:
        :param interval:
        :param limit:
        :return: [
                  [
                    1499040000000,      // 开盘时间
                    "0.01634790",       // 开盘价
                    "0.80000000",       // 最高价
                    "0.01575800",       // 最低价
                    "0.01577100",       // 收盘价(当前K线未结束的即为最新价)
                    "148976.11427815",  // 成交量
                    1499644799999,      // 收盘时间
                    "2434.19055334",    // 成交额
                    308,                // 成交笔数
                    "1756.87402397",    // 主动买入成交量
                    "28.46694368",      // 主动买入成交额
                    "17928899.62484339" // 请忽略该参数
                  ]
                ]
        '''
        method = '/fapi/v1/klines'
        timestamp = str(getTime())
        msg = '&'.join(
            ['symbol=' + symbol, 'interval=' + interval, 'limit=' + str(limit), 'timestamp=' + timestamp])
        signature = self.getSignature(msg)
        response = self.getRequest(method, msg, signature)
        content = json.loads(response.content)
        return content
