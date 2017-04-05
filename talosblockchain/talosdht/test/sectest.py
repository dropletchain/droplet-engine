import unittest

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