import time


def getHumanReadTime(t=None):
    print(t)
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))


print(getHumanReadTime())
