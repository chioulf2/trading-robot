import time
try:
    import thread
except ImportError:
    import _thread as thread


def runOnThread(key):
    def run():
        while True:
            time.sleep(2)
            print('thread', key)

    thread.start_new_thread(run, ())


for i in range(0,3):
    runOnThread(i)

while True:
    time.sleep(2)
    print('Main')

