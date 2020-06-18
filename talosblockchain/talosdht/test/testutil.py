#© 2017-2020, ETH Zurich, D-INFK, lubu@inf.ethz.ch

import base64
import os
import random

import time

from talosstorage.checks import BitcoinVersionedPrivateKey, generate_query_token, get_priv_key
from talosstorage.chunkdata import ChunkData, DoubleEntry, DataStreamIdentifier, create_cloud_chunk

PRIVATE_KEY = BitcoinVersionedPrivateKey("cN5YgNRq8rbcJwngdp3fRzv833E7Z74TsF8nB6GhzRg8Gd9aGWH1")
NONCE = base64.b64decode("OU2HliHRUUZJokNvn84a+A==")
STREAMID = 1
TXID = "8cf71b7ed09acf896b40fc087e56d3d4dbd8cc346a869bb8a81624153c0c2b8c"


def generate_random_chunk(block_id, key=os.urandom(32), size=1000, min_val=0, max_val=30):
    chunk = ChunkData()
    for i in range(size):
        entry = DoubleEntry(int(time.time()), "test", float(random.uniform(min_val, max_val)))
        chunk.add_entry(entry)

    stream_ident = DataStreamIdentifier(PRIVATE_KEY.public_key().address(), STREAMID, NONCE,
                                        TXID)

    return create_cloud_chunk(stream_ident, block_id, get_priv_key(PRIVATE_KEY), 10, key, chunk)


def generate_token(block_id, nonce):
    owner = PRIVATE_KEY.public_key().address()
    stream_ident = DataStreamIdentifier(owner, STREAMID, NONCE,
                                        TXID)
    return generate_query_token(owner, STREAMID, nonce, stream_ident.get_key_for_blockid(block_id), PRIVATE_KEY)