import pika
import json
from config import globalVar
from method import addUser


class MessageQueue(object):

    def __init__(self, strategy):
        self.strategy = strategy
        # 创建socket实例，声明管道
        connect = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
        channel = connect.channel()
        result = channel.queue_declare(queue='register')
        queue_name = result.method.queue
        channel.basic_consume(queue_name, self.callback, True)
        print(' [*] Waiting for messages. To exit press CTRL+C')
        channel.start_consuming()

    def callback(self, ch, method, properties, body):
        userInfo = json.loads(body)
        print(" [x] Received %r" % userInfo)
        # 提交到数据库
        dbConn = globalVar['dbConn']
        cursor = dbConn.cursor()
        sql = '''
                INSERT INTO `user` ( 'api_key', 'secret_key', 'notifyUid', 'quantity', 'level', 'iphone', 'name')
                    VALUES
                ( %s, %s, %s, %s, %s, %s, %s);
        '''
        val = (
            userInfo['apiKey'], userInfo['secretKey'], userInfo['notifyUid'], userInfo['quantity'],
            userInfo['leverage'],
            userInfo['contact'], userInfo['username'])
        cursor.execute(sql, val)
        dbConn.commit()
        # 添加用户实例
        addUser(self.strategy,
                [userInfo['apiKey'], userInfo['secretKey'], userInfo['notifyUid'], userInfo['quantity'],
                 userInfo['leverage']])
