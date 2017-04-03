import requests
import time
import base64
import unittest
import os
import binascii

from talosstorage.checks import generate_query_token, get_priv_key
from talosstorage.chunkdata import ChunkData, DoubleEntry, DataStreamIdentifier, create_cloud_chunk, \
    CloudChunk
from pybitcoin import BitcoinPrivateKey

JSON_TIMESTAMP = "unix_timestamp"
JSON_CHUNK_IDENT = "chunk_key"
JSON_SIGNATURE = "signature"


class BitcoinVersionedPrivateKey(BitcoinPrivateKey):
    _pubkeyhash_version_byte = 111


PRIVATE_KEY = BitcoinVersionedPrivateKey("cRR1K6arfF5TtVxDZzAaf3EmXkhymqrteUPbfDvLHdJr753kPM1m")
NONCE = base64.b64decode("YnoT+AJ20SgZFG67exkf1w==")
STREAMID = 1
TXID = "8fd55b2955757337475c727f60de322b3b03fb8c32dc6ca51723eb0748a1d414"


def store_chunk(chunkid, chunk, ip="127.0.0.1", port=13000):
    req = requests.post("http://%s:%d/store_chunk" % (ip, port), data=chunk.encode())
    return req.reason, req.status_code


def get_nonce_peer(ip, port):
    url = "http://%s:%d/get_chunk" % (ip, port)
    req = requests.get(url)
    return req.reason, req.status_code, req.content


def get_chunk_peer(json_token, ip, port):
    url = "http://%s:%d/get_chunk" % (ip, port)
    req = requests.post(url, json=json_token)
    return req.reason, req.status_code, req.text


def get_chunk_addr(chunk_key, ip="127.0.0.1", port=13000):
    url = "http://%s:%d/chunk_address/%s" % (ip, port, binascii.hexlify(chunk_key))
    req = requests.get(url)
    return req.reason, req.status_code, req.text


def generate_random_chunk(block_id, key=os.urandom(32), size=1000):
    chunk = ChunkData()
    for i in range(size):
        entry = DoubleEntry(int(time.time()), "test", float(i))
        chunk.add_entry(entry)

    stream_ident = DataStreamIdentifier(PRIVATE_KEY.public_key().address(), STREAMID, NONCE,
                                        TXID)

    return create_cloud_chunk(stream_ident, block_id, get_priv_key(PRIVATE_KEY), 10, key, chunk)


def generate_token(nonce):
    owner = PRIVATE_KEY.public_key().address()
    stream_ident = DataStreamIdentifier(owner, STREAMID, NONCE,
                                        TXID)
    return generate_query_token(owner, STREAMID, nonce, stream_ident.get_key_for_blockid(0), PRIVATE_KEY)



class TestStorageApi(unittest.TestCase):

    def _test_get_chunk_for_blockid(self, owner, stream_ident, block_Id):
        a, b, address = get_chunk_addr(stream_ident.get_key_for_blockid(block_Id))
        self.assertEquals(b, 200)
        self.assertTrue(not address is None)
        [ip, port] = address.split(':')
        a, b, nonce = get_nonce_peer(ip, int(port))
        self.assertEquals(b, 200)
        self.assertTrue(not nonce is None)
        nonce = str(nonce)
        token = generate_query_token(owner, STREAMID, nonce, stream_ident.get_key_for_blockid(block_Id), PRIVATE_KEY)
        a, b, chunk = get_chunk_peer(token.to_json(), ip, int(port))
        self.assertEquals(b, 200)
        self.assertTrue(not nonce is None)
        return chunk

    def test_basic(self):
        key = os.urandom(32)
        chunk = generate_random_chunk(0, key=key)
        a, b = store_chunk(0, chunk)
        self.assertEquals(b, 200)

    def test_get(self):
        owner = PRIVATE_KEY.public_key().address()
        stream_ident = DataStreamIdentifier(owner, STREAMID, NONCE,
                                            TXID)

        self._test_get_chunk_for_blockid(owner, stream_ident, 0)

    def test_multiple(self):
        for i in range(0, 100):
            key = os.urandom(32)
            chunk = generate_random_chunk(i, key=key)
            _, code = store_chunk(i, chunk)
            self.assertEquals(code, 200)

            owner = PRIVATE_KEY.public_key().address()
            stream_ident = DataStreamIdentifier(owner, STREAMID, NONCE,
                                                TXID)
            chunk_after = self._test_get_chunk_for_blockid(owner, stream_ident, i)
            # print "before: %s after %s" % (chunk.get_base64_encoded(), base64.b64encode(chunk_after))

            def to_hex(s):
                return ":".join("{:02x}".format(ord(c)) for c in s)
            #print "before: %s \nafter %s" % (to_hex(chunk.encode()), to_hex(chunk_after))
            self.assertEquals(to_hex(chunk_after), to_hex(chunk.encode()))
            print "OK %d" % i
