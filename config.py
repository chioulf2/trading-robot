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
        'init_time': init_time,  # 初始化时间
        'userConfig': userConfig,  # 用户配置: api-key, secret-key, notify-uid, 开仓数, 合约倍数
        'defaultUser': defaultUser,  # 默认用户，用于监听k线数据
        'dbConn': dbConn,
    }


# 全局变量
globalVar = config()
