import argparse

import sys

from twisted.internet import reactor
from twisted.python import log

from talosdht.asyncpolicy import AsyncPolicyApiClient
from talosdht.dhtstorage import TalosLevelDBDHTStorage
from talosdht.server import TalosDHTServer, TalosSecureDHTServer

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Run storage server client")
    parser.add_argument('--dhtport', type=int, help='dhtport', default=14002, required=False)
    parser.add_argument('--dhtserver', type=str, help='dhtserver', default="127.0.0.1", required=False)
    parser.add_argument('--dhtdbpath', type=str, help='dhtdbpath', default="./dhtdbonly", required=False)
    parser.add_argument('--bootstrap', type=str, help='bootstrap', default=None, nargs='*', required=False)
    parser.add_argument('--ksize', type=int, help='ksize', default=10, required=False)
    parser.add_argument('--alpha', type=int, help='alpha', default=3, required=False)
    parser.add_argument('--vcport', type=int, help='vcport', default=5000, required=False)
    parser.add_argument('--vcserver', type=str, help='vcserver', default="127.0.0.1", required=False)
    parser.add_argument('--dht_cache_file', type=str, help='dht_cache_file', default=None, required=False)
    parser.add_argument('--store_state_file', type=str, help='store_state_file', default="./dhtstate.state",
                        required=False)
    parser.add_argument('--logfile', type=str, help='logfile', default=None,
                        required=False)
    parser.add_argument('--secure', dest='secure', action='store_true')
    parser.set_defaults(secure=False)
    args = parser.parse_args()

    f = None
    if args.logfile is None:
        log.startLogging(sys.stdout)
    else:
        f = open(args.logfile, 'w')
        log.startLogging(f)

    storage = TalosLevelDBDHTStorage(args.dhtdbpath)
    vc_server = AsyncPolicyApiClient(ip=args.vcserver, port=args.vcport)

    if args.dht_cache_file is None:
        if args.secure:
            server = TalosSecureDHTServer(ksize=args.ksize, alpha=args.alpha, storage=storage,
                                          talos_vc=vc_server)
        else:
            server = TalosDHTServer(ksize=args.ksize, alpha=args.alpha, storage=storage,
                                    talos_vc=vc_server)

        if args.bootstrap is None:
            server.bootstrap([("1.2.3.4", args.dhtport)])
        else:
            server.bootstrap([(x, int(y)) for (x, y) in map(lambda tmp: tmp.split(':'), args.bootstrap)])
    else:
        if args.secure:
            server = TalosSecureDHTServer.loadState(args.dht_cache_file, storage=storage, talos_vc=vc_server)
        else:
            server = TalosDHTServer.loadState(args.dht_cache_file, storage=storage, talos_vc=vc_server)

    server.listen(args.dhtport, interface=args.dhtserver)
    server.saveStateRegularly(args.store_state_file)

    reactor.run()
