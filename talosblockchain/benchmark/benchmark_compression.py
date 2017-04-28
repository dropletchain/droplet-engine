import argparse
import os
import re
import time
import datetime

from benchmarklogger import FileBenchmarkLogger, SQLLiteBenchmarkLogger
from talosstorage.chunkdata import ChunkData, DoubleEntry, compress_data, MultiDoubleEntry, TYPE_MULTI_DOUBLE_ENTRY, \
    TYPE_MULTI_INT_ENTRY, MultiIntegerEntry
from talosstorage.timebench import TimeKeeper

pattern_data = re.compile("(.*).csv")


def date_to_unixstamp(date_str):
    return int(time.mktime(datetime.datetime.strptime(date_str, "%Y-%m-%d").timetuple()))


def to_string_id(number):
    if number < 10:
        return "0%d" % number
    else:
        return "%d" %number


def extract_eth_plug_data(data_dir, chunk_size, set_id, plug_id):
    cur_chunk = ChunkData(max_size=chunk_size)
    dir_set = os.path.join(data_dir, to_string_id(set_id))
    if os.path.isdir(dir_set):
        files_plug = os.path.join(dir_set, to_string_id(plug_id))
        if os.path.isdir(files_plug):

            for day_file in sorted(os.listdir(files_plug)):
                print day_file
                match = pattern_data.match(day_file)
                if match:
                    timestamp = date_to_unixstamp(match.group(1))
                    with open(os.path.join(files_plug, day_file), 'r') as data_feed:
                        for line in data_feed:
                            data_item = DoubleEntry(timestamp, "device-%d-%d" % (set_id, plug_id), float(line))
                            if not cur_chunk.add_entry(data_item):
                                yield cur_chunk
                                cur_chunk = ChunkData(max_size=chunk_size)
                                cur_chunk.add_entry(data_item)
                            timestamp += 1
    if len(cur_chunk.entries) > 0:
        yield cur_chunk


def extract_eth_smartmeter_data(data_dir, chunk_size):
    cur_chunk = ChunkData(max_size=chunk_size, entry_type=TYPE_MULTI_INT_ENTRY)
    for day_file in sorted(os.listdir(data_dir)):
        print day_file
        match = pattern_data.match(day_file)
        if match:
            timestamp = date_to_unixstamp(match.group(1))
            with open(os.path.join(data_dir, day_file), 'r') as data_feed:
                for line in data_feed:
                    values = map(lambda x: int(float(x) * 10), line.split(","))
                    data_item = MultiIntegerEntry(timestamp, "sm-h1", values)
                    if not cur_chunk.add_entry(data_item):
                        yield cur_chunk
                        cur_chunk = ChunkData(max_size=chunk_size, entry_type=TYPE_MULTI_INT_ENTRY)
                        cur_chunk.add_entry(data_item)
                    timestamp += 1
    if len(cur_chunk.entries) > 0:
        yield cur_chunk


if __name__ == "__main__":
    default_chunk_sizes = [1 << i for i in range(1, 19)]
    parser = argparse.ArgumentParser("Run benchmark")
    parser.add_argument('--chunk_sizes', nargs='+', type=int, default=[86401], required=False)
    parser.add_argument('--log_db', type=str, help='log_db', default=None, required=False)
    parser.add_argument('--name', type=str, help='name', default="COMPRESSION_ETH_PLUG", required=False)
    parser.add_argument('--data_path', type=str, help="data_path", default="/Users/lukas/Documents/MSThesis/blockchain/raw-data/ECOSmart", required=False)
    parser.add_argument('--do_smartmeter', type=bool, help='do_smartmeter', default=True, required=False)
    args = parser.parse_args()

    LOGGING_FIELDS = ["num_chunk_entries", "size_before", "size_compressed"]

    if args.log_db is None:
        logger = FileBenchmarkLogger("%s.log" % (args.name,), LOGGING_FIELDS)
    else:
        logger = SQLLiteBenchmarkLogger(args.log_db, LOGGING_FIELDS, "%s" % (args.name,))

    try:
        for chunk_size in args.chunk_sizes:
            time_keeper = TimeKeeper()
            size_plain = 0
            size_compressed = 0
            if args.do_smartmeter:
                for chunk in extract_eth_smartmeter_data(args.data_path, chunk_size):
                    encoded = chunk.encode()
                    data_compressed = compress_data(encoded)
                    print "Before: %d After: %d" % (len(encoded), len(data_compressed))
                    size_plain += len(encoded)
                    size_compressed += len(data_compressed)
                for chunk in extract_eth_plug_data(args.data_path, chunk_size, 1, 1):
                    encoded = chunk.encode()
                    data_compressed = compress_data(encoded)
                    print "Before: %d After: %d" % (len(encoded), len(data_compressed))
                    size_plain += len(encoded)
                    size_compressed += len(data_compressed)
            time_keeper.store_value("num_chunk_entries", chunk_size)
            time_keeper.store_value("size_before", size_plain)
            time_keeper.store_value("size_compressed", size_compressed)
            logger.log_times_keeper(time_keeper)
    finally:
        logger.close()
