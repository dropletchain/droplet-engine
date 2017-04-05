import unittest
from timeit import default_timer as timer

from talosdht.protocolsecurity import *

class TestStorageApi(unittest.TestCase):

    def test_encoding(self):
        key, nodeid = generate_keys_with_crypto_puzzle(10)

        ser_priv = serialize_priv_key(key)
        ser_pub = serialize_pub_key(key.public_key())

        key_priv_after = deserialize_priv_key(ser_priv)
        key_pub_after = deserialize_pub_key(ser_pub)

        self.assertEquals(serialize_priv_key(key_priv_after), ser_priv)
        self.assertEquals(serialize_pub_key(key_pub_after), ser_pub)

    def test_puzzles(self):
        key, nodeid = generate_keys_with_crypto_puzzle(10)
        x = generate_token_with_puzzle(nodeid, 10)
        self.assertEquals(len(nodeid), len(x))

    def test_benchmark(self):
        def get_time():
            return int(time.time()*1000)

        key, nodeid = generate_keys_with_crypto_puzzle(10)
        pub = key.public_key()
        ip = "127.0.0.1"
        port = 1000
        avg_sig = 0.0
        avg_ver = 0.0
        for i in range(1000):
            cur_time = timer()
            signature, timestamp = sign_msg(ip, port, key)
            time_sig = timer() - cur_time
            avg_sig += time_sig

            cur_time = timer()
            check_msg(ip, port, timestamp, signature, pub)
            time_ver = timer() - cur_time
            avg_ver += time_ver
            print "Time Signature %s ms, Time Verify %s ms" % (time_sig*1000, time_ver*1000)
        avg_ver /= 1000.0
        avg_sig /= 1000.0
        print "Avg Time Signature %s ms, Avg Time Verify %s ms" % (avg_sig * 1000, avg_ver * 1000)
