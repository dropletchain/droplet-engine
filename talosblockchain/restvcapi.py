import json
import argparse

from flask import Flask

from talosvc.config import get_working_db
from talosvc.talosvirtualchain import sync_blockchain
from talosvc.restapi import app, conf, set_sync_interval


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Run bitcoin client")
    parser.add_argument('--port', type=int, help='dir', default=18332, required=False)
    parser.add_argument('--server', type=str, help='server', default="127.0.0.1", required=False)
    parser.add_argument('--rpcuser', type=str, help='rpcuser', default='talos', required=False)
    parser.add_argument('--rpcpw', type=str, help='rpcpw', default='talos', required=False)
    parser.add_argument('--p2pport', type=int, help='p2pport', default=18444, required=False)
    parser.add_argument('--sync', type=int, help='sync', default=60, required=False)
    args = parser.parse_args()

    conf['bitcoind_port'] = args.port
    conf['bitcoind_user'] = args.rpcuser
    conf['bitcoind_passwd'] = args.rpcpw
    conf['bitcoind_server'] = args.server
    conf['bitcoind_p2p_port'] = args.p2pport
    set_sync_interval(args.sync)
    print get_working_db()
    print "Running with conf %s " % conf

    sync_blockchain(conf)
    print "Sync done"
    app.run(debug=False, host='0.0.0.0')




