import argparse
import os
import re
import time
import datetime

from benchmarklogger import FileBenchmarkLogger, SQLLiteBenchmarkLogger
from talosstorage.chunkdata import ChunkData, DoubleEntry, compress_data
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
            for day_file in os.listdir(files_plug):
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Run benchmark")
    parser.add_argument('--chunk_sizes', nargs='+', type=int, default=[86401], required=False)
    parser.add_argument('--log_db', type=str, help='log_db', default=None, required=False)
    parser.add_argument('--name', type=str, help='name', default="COMPRESSION_ETH_PLUG", required=False)
    parser.add_argument('--data_path', type=str, help="data_path", default="/Users/lukas/Documents/MSThesis/blockchain/raw-data/ECOData", required=False)
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
            for chunk in extract_eth_plug_data(args.data_path, chunk_size, 1, 1):
                encoded = chunk.encode()
                size_plain += len(encoded)
                size_compressed += len(compress_data(encoded))
            time_keeper.store_value("num_chunk_entries", chunk_size)
            time_keeper.store_value("size_before", size_plain)
            time_keeper.store_value("size_compressed", size_compressed)
            logger.log_times_keeper(time_keeper)
    finally:
        logger.close()
