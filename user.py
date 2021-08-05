import time
from binanceApi import BinanceApi
from notify import NotifyService


class User(object):

    def __init__(self, api_key, secret_key, notifyUid, quantity='0.05'):
        self.api_key = api_key
        self.secret_key = secret_key
        self.notifyUid = notifyUid
        if quantity == '':
            quantity = '0.05'
        self.quantity = quantity
        self.notifier = NotifyService(notifyUid)
        self.api = BinanceApi(api_key, secret_key)
        self.init_balance = self.api.getBalance()  # 初始资产
        self.last_balance = self.init_balance  # 上次平仓时的资产
        self.balance = self.init_balance  # 当前资产
        self.profit_count = 0  # 盈利次数
        self.loss_count = 0  # 亏损次数
        self.orderMap = {}  # 止盈止损订单对
        self.position = None  # 是否持仓：'long', 'short', None
        self.last_time = time.time()  # 上次平仓时间
        self.leverage = '1'

    def getBalance(self):
        return self.api.getBalance()
