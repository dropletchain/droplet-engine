import argparse
import base64
import os
import random
import sys
import threading
import time

import re

import datetime

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))

from benchmarklogger import SQLLiteBenchmarkLogger, FileBenchmarkLogger
from talosdht.client.dhtrestclient import DHTRestClient, DHTRestClientException, TIME_STORE_CHUNK, TIME_FETCH_ADDRESS, \
    TIME_FETCH_NONCE, TIME_FETCH_CHUNK

from talosstorage.checks import get_priv_key
from talosstorage.chunkdata import ChunkData, DoubleEntry, create_cloud_chunk, DataStreamIdentifier, \
    TYPE_MULTI_DOUBLE_ENTRY, MultiDoubleEntry
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


def generate_cloud_chunk(chunk_data, private_key, block_id, stream_identifier, key=os.urandom(32)):

    return create_cloud_chunk(stream_identifier, block_id, get_priv_key(private_key), 0, key, chunk_data)


pattern_data = re.compile("(.*).csv")


def date_to_unixstamp(date_str):
    return int(time.mktime(datetime.datetime.strptime(date_str, "%Y-%m-%d").timetuple()))


def to_string_id(number):
    if number < 10:
        return "0%d" % number
    else:
        return "%d" %number


def extract_eth_smartmeter_data(data_dir, chunk_size, max_entries=None):
    cur_chunk = ChunkData(max_size=chunk_size, entry_type=TYPE_MULTI_DOUBLE_ENTRY)
    num_entries = 0
    for day_file in sorted(os.listdir(data_dir)):
        print day_file
        match = pattern_data.match(day_file)
        if match:
            timestamp = date_to_unixstamp(match.group(1))
            with open(os.path.join(data_dir, day_file), 'r') as data_feed:
                for line in data_feed:
                    values = map(lambda x: float(x), line.split(","))
                    data_item = MultiDoubleEntry(timestamp, "sm-h1", values)
                    num_entries += 1
                    if not cur_chunk.add_entry(data_item):
                        yield cur_chunk
                        cur_chunk = ChunkData(max_size=chunk_size, entry_type=TYPE_MULTI_DOUBLE_ENTRY)
                        cur_chunk.add_entry(data_item)
                    if num_entries is not None:
                        if num_entries == max_entries:
                            break
                    timestamp += 1
        if num_entries is not None:
            if num_entries == max_entries:
                break
    if len(cur_chunk.entries) > 0:
        yield cur_chunk


class Fetchjob(threading.Thread):
    def __init__(self, my_id, results, dht_api_client, roundns, private_key, identifier):
        self.results = results
        self.my_id = my_id
        self.dht_api_client = dht_api_client
        self.identifier = identifier
        self.private_key = private_key
        self.roundns = roundns
        threading.Thread.__init__(self)

    def run(self):
        for block_id in self.roundns:
            try:
                chunk = self.dht_api_client.fetch_chunk(block_id, self.private_key, self.identifier)
                self.results[self.my_id].append(chunk)
            except Exception as e:
                print e
                self.results[self.my_id].append(None)
                continue


def splitting(l, n):
    mod = len(l) % n
    size = len(l) / n
    offset = 0
    for i in xrange(0, len(l) - mod, size):
        if i / size < mod:
            yield l[i + offset:i + offset + size + 1]
            offset += 1
        else:
            yield l[i + offset:i + size + offset]


def run_benchmark_fetch_par(num_rounds, data_path, num_entries, granularity, fetch_granularity, num_threads, out_logger,
                            private_key=BitcoinVersionedPrivateKey(PRIVATE_KEY),
                            policy_nonce=base64.b64decode(NONCE), stream_id=STREAMID,
                            txid=TXID, ip=IP, port=PORT):
    key = os.urandom(32)
    identifier = DataStreamIdentifier(private_key.public_key().address(), stream_id, policy_nonce, txid)

    dht_api_client = DHTRestClient(dhtip=ip, dhtport=port)

    for block_id, chunk_data in enumerate(extract_eth_smartmeter_data(data_path, granularity, max_entries=num_entries)):
        try:
            chunk = generate_cloud_chunk(chunk_data, private_key, block_id, identifier, key=key)
            dht_api_client.store_chunk(chunk)
            print "Store chunk %d Num entries: %d" % (block_id, len(chunk_data.entries))
        except DHTRestClientException as e:
            print "Store round %d error: %s" % (block_id, e)

    num_fetches = num_entries / granularity
    if not num_entries % granularity == 0:
        num_fetches += 1

    for x in xrange(fetch_granularity, num_entries + 1, fetch_granularity):
        num_fetches = x / granularity
        if not x % granularity == 0:
            num_fetches += 1

        for round in range(num_rounds):
            time_keeper = TimeKeeper()
            results = [[]] * num_threads

            if num_fetches / 2 < num_threads:
                temp_threads = num_fetches / 2
                if temp_threads == 0:
                    temp_threads = 1
                print "Num Fetches: %d Temp_threads %d" % (num_fetches, temp_threads)
                threads = [Fetchjob(idx, results, DHTRestClient(dhtip=ip, dhtport=port), block_id, private_key, identifier)
                           for idx, block_id in enumerate(splitting(range(num_fetches), temp_threads))]
            else:
                threads = [Fetchjob(idx, results, DHTRestClient(dhtip=ip, dhtport=port), block_id, private_key, identifier)
                           for idx, block_id in enumerate(splitting(range(num_fetches), num_threads))]
            time_keeper.start_clock()
            map(lambda x: x.start(), threads)
            map(lambda x: x.join(), threads)
            time_keeper.stop_clock("time_fetch_all")
            time_keeper.store_value("num_entries", x)
            time_keeper.store_value("num_blocks", num_fetches)
            time_keeper.store_value("round", round)
            chunks = [item for sublist in results for item in sublist]
            if len(chunks) == num_fetches:
                print "Round %d ok Num results: %d" % (round, num_fetches)
            else:
                print "Round %d ok Num results: %d" % (round, num_fetches)
            for idx, chunk in enumerate(chunks):
                if chunk is None:
                    print "No result for chunk %d " % idx
            out_logger.log_times_keeper(time_keeper)
    print "DONE"


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Run benchmark")
    parser.add_argument('--dhtport', type=int, help='dhtport', default=PORT, required=False)
    parser.add_argument('--dhtserver', type=str, help='dhtserver', default=IP, required=False)
    parser.add_argument('--nonce', type=str, help='nonce', default=NONCE, required=False)
    parser.add_argument('--txid', type=str, help='txid', default=TXID, required=False)
    parser.add_argument('--stream_id', type=int, help='stream_id', default=STREAMID, required=False)
    parser.add_argument('--private_key', type=str, help='private_key', default=PRIVATE_KEY, required=False)
    parser.add_argument('--num_rounds', type=int, help='num_rounds', default=10, required=False)
    parser.add_argument('--log_db', type=str, help='log_db', default=None, required=False)
    parser.add_argument('--name', type=str, help='name', default="CLIENT_STORE_GET", required=False)

    parser.add_argument('--datapath', type=str, help='datapath', default="../../raw-data/EcoSmart", required=False)
    parser.add_argument('--num_entries', type=int, help='num_entries', default=2419200, required=False)
    parser.add_argument('--granularity', type=int, help='granularity', default=86400, required=False)
    parser.add_argument('--fetch_granularity', type=int, help='fetch_granularity', default=86400, required=False)
    parser.add_argument('--num_threads', type=int, help='num_threads', default=16, required=False)
    args = parser.parse_args()

    LOGGING_FIELDS = ["round", "num_entries", "num_blocks", "time_fetch_all"]

    if args.log_db is None:
        logger = FileBenchmarkLogger("%s_%d.log" % (args.name, args.num_rounds), LOGGING_FIELDS)
    else:
        logger = SQLLiteBenchmarkLogger(args.log_db, LOGGING_FIELDS, "%s" % (args.name,))

    try:
        private_key = BitcoinVersionedPrivateKey(args.private_key)
        policy_nonce = base64.b64decode(args.nonce)
        run_benchmark_fetch_par(args.num_rounds, args.datapath, args.num_entries, args.granularity,
                                args.fetch_granularity, args.num_threads, logger,
                                private_key=private_key, policy_nonce=policy_nonce,
                                stream_id=args.stream_id, txid=args.txid,
                                ip=args.dhtserver, port=args.dhtport)
    finally:
        logger.close()