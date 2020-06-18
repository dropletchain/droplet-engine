#© 2017-2020, ETH Zurich, D-INFK, lubu@inf.ethz.ch

import ipfsapi
import re
from timeit import default_timer as timer

IPFS_ADDR_PATTERN = re.compile(".*(/ipfs/.*)/?")


class IPFSStorage:
    def __init__(self, ip='127.0.0.1', port=5001):
        self.api = ipfsapi.connect(ip, port)

    def store_chunk(self, chunk_data):
        return self.api.add_str(str(chunk_data))

    def get_chunk(self, address):

        if re.match(IPFS_ADDR_PATTERN, address):
            ipfs_address = address
        else:
            ipfs_address = "/ipfs/%s" % address
        return self.api.cat(ipfs_address)


def run_ipfs_load(list_of_addresses, ip="127.0.0.1", port=5001):
    storage = IPFSStorage(ip=ip, port=port)
    results = []
    for address in list_of_addresses:
        before = timer()
        chunk = storage.get_chunk(address)
        results.append((timer() - before) * 1000)
    return results


if __name__ == '__main__':
    storage = IPFSStorage(ip='35.159.23.185')
    addr = storage.store_chunk("HelloChunk")
    print addr
    print storage.get_chunk(addr)


