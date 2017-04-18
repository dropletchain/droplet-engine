import argparse
import base64
import os
import random
import time
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))

from benchmarklogger import SQLLiteBenchmarkLogger, FileBenchmarkLogger
from talosdht.client.dhtrestclient import DHTRestClient, DHTRestClientException, TIME_STORE_CHUNK, TIME_FETCH_ADDRESS, \
    TIME_FETCH_NONCE, TIME_FETCH_CHUNK


from talosstorage.checks import get_priv_key
from talosstorage.chunkdata import ChunkData, DoubleEntry, create_cloud_chunk, DataStreamIdentifier
from talosstorage.timebench import TimeKeeper
from talosvc.config import BitcoinVersionedPrivateKey

#########################
# DEFAULT Stream Params #
#########################

PRIVATE_KEY = "cN5YgNRq8rbcJwngdp3fRzv833E7Z74TsF8nB6GhzRg8Gd9aGWH1"
NONCE = "OU2HliHRUUZJokNvn84a+A=="
STREAMID = 1
TXID = "8cf71b7ed09acf896b40fc087e56d3d4dbd8cc346a869bb8a81624153c0c2b8c"
IP = "127.0.0.1"
PORT = 14000


def generate_random_chunk(private_key, block_id, stream_identifier, tag="test", key=os.urandom(32),
                          size=1000, max_float=1000):
    chunk = ChunkData()
    for i in range(size):
        entry = DoubleEntry(int(time.time()), tag, random.uniform(0, max_float))
        chunk.add_entry(entry)
    return create_cloud_chunk(stream_identifier, block_id, get_priv_key(private_key), 0, key, chunk)


def run_benchmark_store_get(num_rounds, out_logger, private_key=BitcoinVersionedPrivateKey(PRIVATE_KEY), policy_nonce=base64.b64decode(NONCE), stream_id=STREAMID,
                            txid=TXID, ip=IP, port=PORT, chunk_size=100000):
    key = os.urandom(32)
    identifier = DataStreamIdentifier(private_key.public_key().address(), stream_id, policy_nonce, txid)

    dht_api_client = DHTRestClient(dhtip=ip, dhtport=port)

    for round_bench in range(num_rounds):
        try:
            time_keeper = TimeKeeper()
            chunk = generate_random_chunk(private_key, round_bench, identifier, key=key, size=chunk_size)
            dht_api_client.store_chunk(chunk, time_keeper=time_keeper)

            chunk = dht_api_client.fetch_chunk(round_bench, private_key, identifier, time_keeper=time_keeper)

            if chunk is None:
                print "Round %d error" % round_bench
            else:
                print "Round %d ok Chunk size: %d" % (round_bench, len(chunk.encode()))

            out_logger.log_times_keeper(time_keeper)
        except DHTRestClientException as e:
            print "Round %d error: %s" % (round_bench, e)
    print "DONE"

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Run benchmark")
    parser.add_argument('--dhtport', type=int, help='dhtport', default=PORT, required=False)
    parser.add_argument('--dhtserver', type=str, help='dhtserver', default=IP, required=False)
    parser.add_argument('--nonce', type=str, help='nonce', default=NONCE, required=False)
    parser.add_argument('--txid', type=str, help='txid', default=TXID, required=False)
    parser.add_argument('--stream_id', type=int, help='stream_id', default=STREAMID, required=False)
    parser.add_argument('--private_key', type=str, help='private_key', default=PRIVATE_KEY, required=False)
    parser.add_argument('--num_rounds', type=int, help='num_rounds', default=100, required=False)
    parser.add_argument('--chunk_size', type=int, help='chunk_size', default=10000, required=False)
    parser.add_argument('--log_db', type=str, help='log_db', default=None, required=False)
    parser.add_argument('--name', type=str, help='name', default="CLIENT_STORE_GET", required=False)
    args = parser.parse_args()

    LOGGING_FIELDS = [TIME_STORE_CHUNK, TIME_FETCH_ADDRESS, TIME_FETCH_NONCE, TIME_FETCH_CHUNK]

    if args.log_db is None:
        logger = FileBenchmarkLogger("%s_%d.log" % (args.name, args.num_rounds), LOGGING_FIELDS)
    else:
        logger = SQLLiteBenchmarkLogger(args.log_db, LOGGING_FIELDS, "%s" % (args.name,))

    try:
        private_key = BitcoinVersionedPrivateKey(args.private_key)
        policy_nonce = base64.b64decode(args.nonce)
        run_benchmark_store_get(args.num_rounds, logger, private_key=private_key, policy_nonce=policy_nonce,
                                stream_id=args.stream_id, txid=args.txid,
                                ip=args.dhtserver, port=args.dhtport, chunk_size=args.chunk_size)
    finally:
        logger.close()
