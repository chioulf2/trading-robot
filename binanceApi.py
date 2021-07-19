import hmac
import hashlib
import requests
import json
from util import getTime


class BinanceApi(object):

    def __init__(self, api_key, secret_key):
        self.secret_key = secret_key
        self.host = "fapi.binance.com"
        self.headers = {
            "X-MBX-APIKEY": api_key
        }
        self.proxies = {
          "http": "http://127.0.0.1:1087",
          "https": "http://127.0.0.1:1087",
        }

    def getSignature(self, msg):
        return hmac.new(bytes(self.secret_key, 'utf-8'), msg=bytes(msg, 'utf-8'), digestmod=hashlib.sha256).hexdigest()

    def getRequest(self, method, msg, signature):
        return requests.get(
            'https://' + self.host + method + '?' + msg + '&signature=' + signature,
            headers=self.headers)

    def postRequest(self, method, msg, signature):
        return requests.post(
            'https://' + self.host + method + '?' + msg + '&signature=' + signature,
            headers=self.headers)

    def deleteRequest(self, method, msg, signature):
        return requests.delete(
            'https://' + self.host + method + '?' + msg + '&signature=' + signature,
            headers=self.headers)

    def getBalance(self):
        method = '/fapi/v2/balance'
        timestamp = str(getTime())
        msg = '&'.join(
            ['timestamp=' + timestamp])
        signature = self.getSignature(msg)
        response = self.getRequest(method, msg, signature)
        content = json.loads(response.content)
        print('资产: ', str(content[1]['balance']), ' U')
        return float(content[1]['balance'])

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
        print('资产: ', str(content['positions']), ' U')
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
        price = self.getPrice(symbol)
        res = self.getUserData(symbol)
        longQuantity = res['long']
        shortQuantity = res['short']
        if longQuantity > 0:
            self.order(symbol, 'SELL', 'LONG', 'MARKET', str(longQuantity), '', str(round(float(price) * 1.2, 2)))
        if shortQuantity > 0:
            self.order(symbol, 'BUY', 'SHORT', 'MARKET', str(shortQuantity), '', str(round(float(price) * 0.8, 2)))

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

    def getKline(self, symbol, interval):
        method = '/fapi/v1/klines'
        timestamp = str(getTime())
        msg = '&'.join(
            ['symbol=' + symbol, 'interval=' + interval, 'limit=200', 'timestamp='+timestamp])
        signature = self.getSignature(msg)
        response = self.getRequest(method, msg, signature)
        content = json.loads(response.content)
        return content
