import os
import argparse
import requests
import numpy as np
import json
from ipfs_util import IPFSStorage, run_ipfs_load
import time
from cStringIO import StringIO


def get_results(server_ip, server_port, addresses):
    content = "\n".join(addresses)
    req = requests.post("http://%s:%d/ipfs_bench" % (server_ip, server_port), data=str(content))
    if req.status_code != 200:
        return None
    return json.loads(req.text)


def store_chunks(chunk_size=1000, num_chunks=100, ip='127.0.0.1', port=5001):
    storage = IPFSStorage(ip=ip, port=port)
    addresses = []
    for round in range(num_chunks):
        cur_chunk = os.urandom(chunk_size)
        address = storage.store_chunk(cur_chunk)
        print "Stored chunk with address:  %s" % address
        addresses.append(address)
    return addresses


def run_remote_benchmark(addresses, server_ip, server_port=12000):
    return get_results(server_ip, server_port, addresses)


def run_ipfs_bench(server_ip, num_retry=3, chunk_size=1000, num_chunks=10, server_port=12000, sleep_time=30):
    addresses = store_chunks(chunk_size=chunk_size, num_chunks=num_chunks)
    print "Wait for %d seconds" % sleep_time
    time.sleep(sleep_time)
    times = []
    for iter in range(num_retry):
        temporary_results = run_remote_benchmark(addresses, server_ip, server_port=server_port)
        times.append(temporary_results)
    return times


def run_ipfs_bench_remote(server_store_ip, server_fetch_ips, server_store_port=5001, server_fetch_port=5001,
                chunk_size = 1000, num_chunks = 10, sleep_time=20):
    addresses = store_chunks(chunk_size=chunk_size, num_chunks=num_chunks, ip=server_store_ip, port=server_store_port)
    print "Wait for %d seconds" % sleep_time
    time.sleep(sleep_time)
    times = []
    for server_fetch_ip in server_fetch_ips:
        temporary_results = run_ipfs_load(addresses, ip=server_fetch_ip, port=server_fetch_port)
        times.append(temporary_results)
    return times

def run_ipfs_bench_2(addresses, server_fetch_ip,server_fetch_port=5001, num_retry = 3):
    times = []
    for iter in range(num_retry):
        temporary_results = run_ipfs_load(addresses, ip=server_fetch_ip, port=server_fetch_port)
        times.append(temporary_results)
    return times


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Do Benchmark")
    parser.add_argument('--port', type=int, help='port', default=5001, required=False)
    parser.add_argument('--ipfetch', nargs='+', help='ipfetch', default=["35.159.23.185"], required=False)
    parser.add_argument('--ipstore', type=str, help='ip', default="54.213.148.163", required=False)
    parser.add_argument('--chunksize', type=int, help='chunksize', default=8192, required=False)
    parser.add_argument('--numchunks', type=int, help='numchunks', default=100, required=False)
    parser.add_argument('--retries', type=int, help='retries', default=3, required=False)
    args = parser.parse_args()

    times = run_ipfs_bench_remote(args.ipstore, args.ipfetch, server_store_port=args.port, server_fetch_port=args.port,
                                  num_retry=args.retries, chunk_size=args.chunksize, num_chunks=args.numchunks)
    res = np.asarray(times).transpose()
    s = StringIO()
    np.savetxt(s, res, fmt='%f', delimiter=",")
    print s.getvalue()

    with open("%d_ipfs_bench_%d_iter.csv" % (args.chunksize, args.numchunks), 'w') as log_file:
        log_file.write(s.getvalue())
