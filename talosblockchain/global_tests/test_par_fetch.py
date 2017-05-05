from multiprocessing.pool import ThreadPool
from time import time as timer, sleep

from urllib2 import urlopen


def do_work((a,b,c)):
    sleep(1)
    print "%s, %s, %s" % (a,b,c)
    return a, b, c


pool = ThreadPool(20)
start = timer()
try:
    res = pool.map(do_work, [(1,2,3), (4,5,6), (7,8,9)])
    print res
    for x in res:
        print x
    print "Elapsed Time: %s" % (timer() - start,)
    res = pool.map(do_work, [(1, 2, 3), (4, 5, 6), (7, 8, 9)])
    print res



finally:
    pool.terminate()
    pool.close()