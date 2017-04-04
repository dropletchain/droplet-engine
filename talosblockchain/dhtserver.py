import argparse

import sys

from twisted.internet import reactor
from twisted.python import log
from twisted.web.resource import Resource
from twisted.web.server import Site

from talosdht.asyncpolicy import AsyncPolicyApiClient
from talosdht.dhtrestapi import AddChunk, GetChunkLoaction
from talosdht.dhtstorage import TalosLevelDBDHTStorage
from talosdht.server import TalosDHTServer

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Run storage server client")
    parser.add_argument('--dhtport', type=int, help='dhtport', default=13001, required=False)
    parser.add_argument('--dhtserver', type=str, help='dhtserver', default="", required=False)
    parser.add_argument('--restport', type=int, help='restport', default=13000, required=False)
    parser.add_argument('--restserver', type=str, help='restserver', default="127.0.0.1", required=False)
    parser.add_argument('--dhtdbpath', type=str, help='dhtdbpath', default="./dhtdb", required=False)
    parser.add_argument('--bootstrap', type=str, help='bootstrap', default=None, nargs='*', required=False)
    parser.add_argument('--ksize', type=int, help='ksize', default=10, required=False)
    parser.add_argument('--alpha', type=int, help='alpha', default=10, required=False)
    parser.add_argument('--vcport', type=int, help='vcport', default=5000, required=False)
    parser.add_argument('--vcserver', type=str, help='vcserver', default="127.0.0.1", required=False)
    parser.add_argument('--dht_cache_file', type=str, help='dht_cache_file', default=None, required=False)
    args = parser.parse_args()

    log.startLogging(sys.stdout)

    storage = TalosLevelDBDHTStorage(args.dhtdbpath)
    vc_server = AsyncPolicyApiClient(ip=args.vcserver, port=args.vcport)

    if args.dht_cache_file is None:
        server = TalosDHTServer(ksize=args.ksize, alpha=args.alpha, storage=storage,
                                talos_vc=vc_server)
        if args.bootstrap is None:
            server.bootstrap([("1.2.3.4", args.dhtport)])
        else:
            server.bootstrap([(x, int(y)) for (x, y) in map(lambda tmp: tmp.split(':'), args.bootstrap)])
    else:
        server = TalosDHTServer.loadState(args.dht_cache_file)

    server.listen(args.dhtport, interface=args.dhtserver)

    root = Resource()
    root.putChild("store_chunk", AddChunk(server))
    root.putChild("chunk_address", GetChunkLoaction(server))

    factory = Site(root)
    reactor.listenTCP(args.restport, factory, interface=args.restserver)
    reactor.run()
