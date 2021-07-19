import time

try:
    import thread
except ImportError:
    import _thread as thread


class A(object):

    def __init__(self):
        self.a = 'a'

    def runOnThread(self, key):
        def run():
            while True:
                time.sleep(2)
                print('thread', key, self.a)

        thread.start_new_thread(run, ())


for i in range(0, 3):
    a = A()
    a.runOnThread(i)

while True:
    time.sleep(2)
    print('Main')
