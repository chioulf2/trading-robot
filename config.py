import json
import time
from dbConnect import getDBConn
from user import User


def config():
    # 交易所API配置
    file = open('./config.json', 'r')
    c = json.loads(file.read())
    secret_key = c['secret_key']
    headers = c['headers']
    api_key = headers['X-MBX-APIKEY']
    notifyUid = c['notifyUid']
    defaultUser = User(api_key, secret_key, notifyUid, '')

    dbConn = getDBConn()
    cursor = dbConn.cursor()
    cursor.execute("select * from `user`")
    userConfig = cursor.fetchall()
    dbConn.commit()
    print(userConfig)

    # 交易信息配置
    symbol = 'ETHUSDT'  # 交易对
    init_time = time.time()  # 开机时间

    return {
        'symbol': symbol,  # 交易对象
        'mode': 'trendOver',  # 模式: 分为 "trendOver（趋势结束）", "trendUp(趋势上涨)", "trendDown(趋势下跌)", "shockUp(震荡上涨)", "shockDown(震荡下跌)"
        'kline15m': [],    # 15分钟k线数据
        'kline30m': [],    # 30分钟k线数据
        'init_time': init_time,  # 初始化时间
        'klineTime': init_time,  # 15分钟k线监听间隔时间，用于控制采样频率
        'listenTime': init_time,   # 15分钟k线监听的重启时间，用于控制重启监听服务，每23小时重启一次
        'kline30mTime': init_time,  # 30分钟k线监听间隔时间，用于控制采样频率
        'listen30mTime': init_time,  # 30分钟k线监听的重启时间，用于控制重启监听服务，每23小时重启一次
        'userConfig': userConfig,  # 用户配置: api-key, secret-key, notify-uid, 开仓数, 合约倍数
        'defaultUser': defaultUser,  # 默认用户，用于监听k线数据
        'dbConn': dbConn,
        'isNeedleMarket': False,
        'P': 2,  # 布林线标准差
    }


# 全局变量
globalVar = config()
