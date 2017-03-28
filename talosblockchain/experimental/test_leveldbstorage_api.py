import requests
import time
import base64
import unittest
import os

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
STREAMID=1
TXID="8fd55b2955757337475c727f60de322b3b03fb8c32dc6ca51723eb0748a1d414"


def store_chunk(chunkid, chunk, ip="127.0.0.1", port=12000):
    req = requests.post("http://%s:%d/store_chunk/%d" % (ip, port, chunkid), data=chunk.encode())
    return req.reason, req.status_code


def get_chunk(json_token, ip="127.0.0.1", port=12000):
    url = "http://%s:%d/get_chunk" % (ip, port)
    req = requests.post(url, json=json_token)
    return req.reason, req.status_code, req.text


def generate_random_chunk(block_id, key=os.urandom(32), size=1000):
    chunk = ChunkData()
    for i in range(size):
        entry = DoubleEntry(int(time.time()), "test", float(i))
        chunk.add_entry(entry)

    stream_ident = DataStreamIdentifier(PRIVATE_KEY.public_key().address(), STREAMID, NONCE,
                                        TXID)

    return create_cloud_chunk(stream_ident, block_id, get_priv_key(PRIVATE_KEY), 10, key, chunk)


def generate_token():
    owner = PRIVATE_KEY.public_key().address()
    stream_ident = DataStreamIdentifier(owner, STREAMID, NONCE,
                                        TXID)
    return generate_query_token(owner, STREAMID, stream_ident.get_key_for_blockid(0), PRIVATE_KEY)


class TestStorageApi(unittest.TestCase):

    def test_basic(self):
        key = os.urandom(32)
        chunk = generate_random_chunk(0, key=key)
        store_chunk(0, chunk)

    def test_get(self):
        owner = PRIVATE_KEY.public_key().address()
        stream_ident = DataStreamIdentifier(owner, STREAMID, NONCE,
                                            TXID)
        token = generate_query_token(owner, STREAMID, stream_ident.get_key_for_blockid(0), PRIVATE_KEY)
        a, b, chunk = get_chunk(token)
        self.assertEquals(b, 200)
        chunk = CloudChunk.decode(chunk)
        print chunk.key
