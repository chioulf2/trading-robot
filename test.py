# import time
# import asyncio
#
#
# async def setTimeout(cb, arg, delay):
#     await asyncio.sleep(delay)
#     cb(arg)
#
#
# def consoleLog(msg):
#     print(time.time(), msg)
#
#
# async def main():
#     for i in range(6):
#         await setTimeout(consoleLog, i, 1)
#
#
# asyncio.run(main())
