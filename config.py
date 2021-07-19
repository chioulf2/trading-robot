import json
import time
from dbConnect import userConfig
from user import User

# 交易所API配置
file = open('./config.json', 'r')
config = json.loads(file.read())
host = config['host']
secret_key = config['secret_key']
headers = config['headers']
api_key = headers['X-MBX-APIKEY']
notifyUid = config['notifyUid']
defaultUser = User(api_key, secret_key, notifyUid)

# 交易信息配置
symbol = 'ETHUSDT'  # 交易对
quantity = '0.05'  # 交易量
leverage = '1'  # 合约倍数
init_time = time.time()  # 开机时间
interval = '15m'  # 15分钟k线
# 盈利次数，亏损次数，当前时间，当前资产，止盈止损订单对
globalVar = {'mode': 'trendOver', 'kline': [], 'userConfig': userConfig, 'userMap': {},'defaultUser': defaultUser}
