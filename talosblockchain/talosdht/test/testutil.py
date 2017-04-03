import base64
import os
import random

import time

from talosstorage.checks import BitcoinVersionedPrivateKey, generate_query_token, get_priv_key
from talosstorage.chunkdata import ChunkData, DoubleEntry, DataStreamIdentifier, create_cloud_chunk

PRIVATE_KEY = BitcoinVersionedPrivateKey("cRR1K6arfF5TtVxDZzAaf3EmXkhymqrteUPbfDvLHdJr753kPM1m")
NONCE = base64.b64decode("YnoT+AJ20SgZFG67exkf1w==")
STREAMID=1
TXID="8fd55b2955757337475c727f60de322b3b03fb8c32dc6ca51723eb0748a1d414"


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