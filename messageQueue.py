import pika
import json
from config import globalVar
from method import addUser, removeUser


class MessageQueue(object):

    def __init__(self, strategy, webSocketPool):
        self.strategy = strategy
        self.webSocketPool = webSocketPool
        # 创建socket实例，声明管道
        connect = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
        self.channel = connect.channel()
        self.subscribe('register', self.register)
        self.subscribe('start', self.start)
        self.subscribe('stop', self.stop)
        print(' [*] Waiting for messages. To exit press CTRL+C')
        self.channel.start_consuming()

    def subscribe(self, topic, callback):
        result = self.channel.queue_declare(queue=topic)
        queue_name = result.method.queue
        self.channel.basic_consume(queue_name, callback, True)

    def register(self, ch, method, properties, body):
        userInfo = json.loads(body)
        print(" [x] Received %r" % userInfo)
        # 提交到数据库
        dbConn = globalVar['dbConn']
        cursor = dbConn.cursor()
        sql = '''
                INSERT INTO `user` ( 'api_key', 'secret_key', 'wx_uid', 'tg_uid', 'quantity', 'level', 'iphone', 'name')
                    VALUES
                ( %s, %s, %s, %s, %s, %s, %s);
        '''
        val = (
            userInfo['apiKey'], userInfo['secretKey'], userInfo['wxUid'], userInfo['tgUid'], userInfo['quantity'],
            userInfo['leverage'],
            userInfo['contact'], userInfo['username'])
        cursor.execute(sql, val)
        dbConn.commit()
        # 添加用户实例
        addUser(self.strategy, self.webSocketPool,
                [userInfo['apiKey'], userInfo['secretKey'], userInfo['wxUid'], userInfo['tgUid'],
                 userInfo['quantity'],
                 userInfo['leverage']])

    def start(self, ch, method, properties, body):
        userInfo = json.loads(body)
        print(" [x] Received %r" % userInfo)
        # 提交到数据库
        dbConn = globalVar['dbConn']
        cursor = dbConn.cursor()
        cursor.execute('select * from `user` where `wx_uid`=' + userInfo['wxUid'])
        userConfig = cursor.fetchone()
        dbConn.commit()
        if userConfig is not None:
            addUser(self.strategy, self.webSocketPool, userConfig)

    def stop(self, ch, method, properties, body):
        userInfo = json.loads(body)
        print(" [x] Received %r" % userInfo)
        removeUser(self.strategy, self.webSocketPool, userInfo['apiKey'])
