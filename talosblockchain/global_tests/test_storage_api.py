from StringIO import StringIO

import requests
import time
import base64
import unittest
import os
import binascii

from timeit import default_timer as timer

from PIL import Image

from talosstorage.checks import generate_query_token, get_priv_key
from talosstorage.chunkdata import ChunkData, DoubleEntry, DataStreamIdentifier, create_cloud_chunk, \
    CloudChunk, get_chunk_data_from_cloud_chunk, TYPE_PICTURE_ENTRY, PictureEntry
from pybitcoin import BitcoinPrivateKey

JSON_TIMESTAMP = "unix_timestamp"
JSON_CHUNK_IDENT = "chunk_key"
JSON_SIGNATURE = "signature"


class BitcoinVersionedPrivateKey(BitcoinPrivateKey):
    _pubkeyhash_version_byte = 111


#PRIVATE_KEY = BitcoinVersionedPrivateKey("cRR1K6arfF5TtVxDZzAaf3EmXkhymqrteUPbfDvLHdJr753kPM1m")
PRIVATE_KEY = BitcoinVersionedPrivateKey("cN5YgNRq8rbcJwngdp3fRzv833E7Z74TsF8nB6GhzRg8Gd9aGWH1")
NONCE = base64.b64decode("OU2HliHRUUZJokNvn84a+A==")
STREAMID = 1
TXID = "8cf71b7ed09acf896b40fc087e56d3d4dbd8cc346a869bb8a81624153c0c2b8c"
IP = "127.0.0.1"
#IP = "46.101.113.112"
#IP = "138.68.191.35"
#PORT = 14000
PORT = 15000

def store_chunk(chunkid, chunk, ip=IP, port=PORT):
    req = requests.post("http://%s:%d/store_chunk" % (ip, port), data=chunk.encode())
    return req.reason, req.status_code


def get_nonce_peer(ip, port):
    url = "http://%s:%d/get_chunk" % (ip, port)
    req = requests.get(url)
    return req.reason, req.status_code, req.content


def get_chunk_peer(json_token, ip, port):
    url = "http://%s:%d/get_chunk" % (ip, port)
    req = requests.post(url, json=json_token)
    return req.reason, req.status_code, req.content


def get_chunk_addr(chunk_key, ip=IP, port=PORT):
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

    def test_get_image(self):
        block_id = 0
        owner = PRIVATE_KEY.public_key().address()
        stream_ident = DataStreamIdentifier(owner, 3, NONCE,
                                            TXID)

        chunk = self._test_get_chunk_for_blockid(owner, stream_ident, block_id)
        print len(chunk)
        chunk_ = CloudChunk.decode(str(chunk))
        data = get_chunk_data_from_cloud_chunk(chunk_, "a"*16)
        print chunk_.get_key_hex()
        print data.entries[0].metadata
        print hash(data.entries[0].picture_data)
        img = Image.open(StringIO(data.entries[0].picture_data))
        img.show()

    def test_tmp(self):
        for i in range(100):
            chunk_tmp = ChunkData(type=TYPE_PICTURE_ENTRY)
            chunk_tmp.add_entry(PictureEntry(int(time.time()), "bla%d" % i, "sdfasdfasdf%d" % i))
            print chunk_tmp.entries[0].metadata
            print hash(chunk_tmp.entries[0].picture_data)

    def test_multiple(self):
        num_iter = 100
        avg_store = 0
        avg_get = 0
        for i in range(0, num_iter):
            key = os.urandom(32)
            chunk = generate_random_chunk(i, key=key, size=10000)
            cur_time = timer()
            _, code = store_chunk(i, chunk)
            store_time = timer() - cur_time
            avg_store += store_time
            self.assertEquals(code, 200)

            owner = PRIVATE_KEY.public_key().address()
            stream_ident = DataStreamIdentifier(owner, STREAMID, NONCE,
                                                TXID)
            cur_time = timer()
            chunk_after = self._test_get_chunk_for_blockid(owner, stream_ident, i)
            get_time = timer() - cur_time
            avg_get += get_time
            # print "before: %s after %s" % (chunk.get_base64_encoded(), base64.b64encode(chunk_after))

            def to_hex(s):
                return ":".join("{:02x}".format(ord(c)) for c in s)
            #print "before: %s \nafter %s" % (to_hex(chunk.encode()), to_hex(chunk_after))
            #self.assertEquals(to_hex(chunk_after), to_hex(chunk.encode()))
            print "OK %d Storetime %s Gettime %s" % (i, store_time, get_time)
        print "Avg store: %s Avg get: %s" % ((avg_store/num_iter) * 1000, (avg_get/num_iter) * 1000)

    def test_gets_only(self):
        num_iter = 100
        avg_get = 0
        for i in range(0, num_iter):
            owner = PRIVATE_KEY.public_key().address()
            stream_ident = DataStreamIdentifier(owner, STREAMID, NONCE,
                                                TXID)
            cur_time=timer()
            chunk_after = self._test_get_chunk_for_blockid(owner, stream_ident, i)
            get_time = timer() - cur_time
            avg_get += get_time

            print "OK %d Length: %d Time %s ms" % (i, len(chunk_after), get_time * 1000)
        print "Avg get: %s" % ((avg_get / num_iter) * 1000)