import time
from binanceApi import BinanceApi
from private.notify import NotifyService


class User(object):

    def __init__(self, user, proxies):
        self.api_key = user['api-key']
        self.secret_key = user['secret-key']
        self.wxPushUid = user['wxPushUid']
        if 'quantity' not in user or user['quantity'] is None or user['quantity'] == '':
            self.quantity = '0.05'
        else:
            self.quantity = user['quantity']
        self.notifier = NotifyService(user['wxPushUid'], user['TgPushUid'])
        self.api = BinanceApi(user['api-key'], user['secret-key'], proxies)
        self.init_balance = self.api.getBalance()  # 初始资产
        self.last_balance = self.init_balance  # 上次平仓时的资产
        self.balance = self.init_balance  # 当前资产
        self.profit_count = 0  # 盈利次数
        self.loss_count = 0  # 亏损次数
        self.orderMap = {}  # 止盈止损订单对
        self.position = None  # 是否持仓：'long', 'short', None
        self.last_close_time = time.time()  # 上次平仓时间
        self.last_open_time = time.time()   # 上次开仓时间
        if 'level' not in user or user['level'] is None or user['level'] == '':
            self.leverage = '1'
        else:
            self.leverage = user['level']

    def getBalance(self):
        return self.api.getBalance()
