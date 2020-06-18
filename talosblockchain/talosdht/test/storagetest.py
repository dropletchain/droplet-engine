#© 2017-2020, ETH Zurich, D-INFK, lubu@inf.ethz.ch

from twisted.trial import unittest

from talosdht.dhtstorage import TalosLevelDBDHTStorage
from talosdht.test.testutil import generate_random_chunk
from talosstorage.checks import BitcoinVersionedPrivateKey
from talosstorage.timebench import TimeKeeper
from talosvc.talosclient.restapiclient import TalosVCRestClient

from timeit import default_timer as timer
import time

class StorageTest(unittest.TestCase):

    def test_storage1(self):
        key = BitcoinVersionedPrivateKey("cN5YgNRq8rbcJwngdp3fRzv833E7Z74TsF8nB6GhzRg8Gd9aGWH1")
        talosStorage = TalosLevelDBDHTStorage("db_tmp")
        client = TalosVCRestClient()
        num_iter = 100
        for i in range(num_iter):
            chunk = generate_random_chunk(i)
            policy = client.get_policy_with_txid(chunk.get_tag_hex())
            before = timer()
            talosStorage.store_check_chunk(chunk, i, policy)
            print "Time store %s" % ((timer() - before) * 1000,)
            keeper = TimeKeeper()
            before = timer()
            talosStorage.get_check_chunk(chunk.key, key.public_key().to_hex(), policy, time_keeper=keeper)
            print "Time get %s" % ((timer() - before) * 1000,)
        count = 0
        for (key, value) in talosStorage.iteritemsOlderThan(100):
            count += 1
        self.assertEquals(0, count)

        count = 0
        for (key, value) in talosStorage.iteritems():
            count += 1
        self.assertEquals(num_iter, count)

        time.sleep(6)
        count = 0
        for (key, value) in talosStorage.iteritemsOlderThan(5):
            count += 1
        self.assertEquals(num_iter, count)

