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
# 模式，k线数据，k线监听时间，用户配置，用户对象，默认用户
globalVar = {'mode': 'trendOver', 'kline': [], 'listenTime': init_time, 'userConfig': userConfig, 'userMap': {},'defaultUser': defaultUser}
