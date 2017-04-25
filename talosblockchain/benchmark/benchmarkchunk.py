import argparse
import random
import time
import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))

from benchmarklogger import SQLLiteBenchmarkLogger, FileBenchmarkLogger
from talosstorage.chunkdata import *


def benchmark_chunks(num_rounds, local_logger, chunk_size, max_float=10000, tag_size=10):
    key = os.urandom(32)
    private_key = ec.generate_private_key(ec.SECP256K1, default_backend())
    stream_ident = DataStreamIdentifier("pubaddr", 3, "asvcgdterategdts",
                                        "59f7a5a9de7a44ad0f8b0cb95faee0a2a43af1f99ec7cab036b737a4c0f911bb")
    for round in range(num_rounds):
        time_keeper = TimeKeeper()
        chunk = ChunkData()
        for i in range(chunk_size):
            entry = DoubleEntry(int(time.time()), "a" * tag_size, random.uniform(0, max_float))
            chunk.add_entry(entry)

        time_keeper.start_clock()
        cd = create_cloud_chunk(stream_ident, round, private_key, 1, key, chunk, time_keeper=time_keeper)
        time_keeper.stop_clock("time_create_chunk")

        time_keeper.start_clock()
        chunk_after = cd.get_and_check_chunk_data(key, time_keeper=time_keeper)
        time_keeper.stop_clock("time_extract_chunk_data")

        time_keeper.store_value("size_before", len(chunk.encode(use_compression=False)))
        time_keeper.store_value("size_cloud", len(cd.encode()))
        local_logger.log_times_keeper(time_keeper)
        print "Round %d done" % round


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Run benchmark chunk")
    parser.add_argument('--num_rounds', type=int, help='num_rounds', default=100, required=False)
    parser.add_argument('--max_float', type=int, help='max_float', default=10000, required=False)
    parser.add_argument('--tag_size', type=int, help='tag_size', default=10, required=False)
    parser.add_argument('--chunk_size', type=int, help='chunk_size', default=10000, required=False)
    parser.add_argument('--log_db', type=str, help='log_db', default=None, required=False)
    parser.add_argument('--name', type=str, help='name', default="CHUNK_LOCAL", required=False)
    args = parser.parse_args()

    LOGGING_FIELDS = ["time_create_chunk", "chunk_compression", "gcm_encryption", "ecdsa_signature",
                      "time_extract_chunk_data", "aes_gcm_decrypt", "zlib_decompression", "size_before", "size_cloud"]

    if args.log_db is None:
        logger = FileBenchmarkLogger("%s_%d.log" % (args.name, args.num_rounds), LOGGING_FIELDS)
    else:
        logger = SQLLiteBenchmarkLogger(args.log_db, LOGGING_FIELDS, "%s" % (args.name,))

    try:
        benchmark_chunks(args.num_rounds, logger, args.chunk_size, max_float=args.max_float, tag_size=args.tag_size)
    finally:
        logger.close()
