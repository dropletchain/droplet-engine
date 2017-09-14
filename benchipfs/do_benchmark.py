import os
import requests
import numpy as np
import json
from ipfs_util import IPFSStorage
import base64
import time
from cStringIO import StringIO


def get_results(server_ip, server_port, addresses):
    content = "\n".join(addresses)
    req = requests.post("http://%s:%d/ipfs_bench" % (server_ip, server_port), data=str(content))
    if req.status_code!=200:
        return None
    return json.loads(req.text)


def store_chunks(chunk_size=1000, num_chunks=100):
    storage = IPFSStorage()
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

if __name__ == "__main__":
    times = run_ipfs_bench('52.59.204.211')
    res = np.asarray(times).transpose()
    s = StringIO()
    np.savetxt(s, res, fmt='%f')
    print s.getvalue()
