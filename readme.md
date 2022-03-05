这是我自研的加密货币量化交易机器人，交易平台是币安，U本位合约，ETH/USDT交易对。

#### 关于配置

private文件夹我没有上传到git，但弄了个private_template文件夹，参考这个文件夹里的文件进行配置

- config.json中存的是默认用户的配置，也就是我自己的
- dbConnect.py用于连接数据库，数据库中存的是用户配置，可以多用户执行这个量化交易
- notify.py是用来给用户发通知的，有两种渠道，一种是微信订阅消息，一种是telegram订阅频道

数据库表user

- active: 代表是否激活，未激活的用户会直接略过
- api-key: 币安api-key
- secret-key: 币安secret-key
- quantity: 开仓数
- level: 合约倍数
- strategy: 使用策略几
- wxPushUid: 微信通知id
- TgPushUid: telegram通知id

config.py中记录了整个项目的配置，比如是否开启代理（访问币安api是要翻墙的），交易哪个交易对（这个以后会挪到用户配置中去）
