import json
import time
from private.dbConnect import getDBConn
from user import User


def config():
    """
    :return:
    """
    # 交易信息配置
    symbol = 'ETHUSDT'  # 交易对
    init_time = time.time()  # 开机时间
    # 访问币安api是否需要设置代理
    proxy = True
    proxies = {}
    if proxy:
        proxies = {
            "http": "http://127.0.0.1:1087",
            "https": "http://127.0.0.1:1087",
        }

    # 交易所API配置
    file = open('private/config.json', 'r')
    c = json.loads(file.read())
    secret_key = c['secret_key']
    headers = c['headers']
    api_key = headers['X-MBX-APIKEY']
    wxPushUid = c['wxPushUid']
    TgPushUid = c['TgPushUid']
    defaultUser = User({
        'api-key': api_key,
        'secret-key': secret_key,
        'wxPushUid': wxPushUid,
        'TgPushUid': TgPushUid
    }, proxies)

    dbConn = getDBConn()
    cursor = dbConn.cursor()
    cursor.execute("select * from `user`")
    userConfig = cursor.fetchall()
    dbConn.commit()
    print(userConfig)
    # 把用户信息从数组解析成对象，写代码时用数组下标根本不知道是哪个字段
    userConfigList = []
    for u in userConfig:
        userConfigList.append({
            'active': u[0],
            'api-key': u[1],
            'secret-key': u[2],
            'quantity': u[3],
            'level': u[4],
            'strategy': u[5],
            'wxPushUid': u[6],
            'TgPushUid': u[7]
        })

    return {
        'symbol': symbol,  # 交易对象
        'init_time': init_time,  # 初始化时间
        'userConfig': userConfigList,  # 用户配置，详情参考readme
        'defaultUser': defaultUser,  # 默认用户，用于监听k线数据
        'dbConn': dbConn,
        'proxies': proxies
    }


# 全局变量
globalVar = config()
