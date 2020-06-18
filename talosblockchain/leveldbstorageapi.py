#© 2017-2020, ETH Zurich, D-INFK, lubu@inf.ethz.ch

import argparse

from talosvc.talosclient.restapiclient import TalosVCRestClient
from talosstorage.restapi import app, set_storage_impl, set_vc_client
from talosstorage.storage import LevelDBStorage

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Run storage server client")
    parser.add_argument('--vcport', type=int, help='dir', default=5000, required=False)
    parser.add_argument('--vcserver', type=str, help='server', default="127.0.0.1", required=False)
    parser.add_argument('--port', type=int, help='dir', default=12000, required=False)
    parser.add_argument('--server', type=str, help='server', default="127.0.0.1", required=False)
    args = parser.parse_args()

    VC_IP = args.vcserver
    VC_PORT = args.vcport

    client = TalosVCRestClient(ip=args.vcserver, port=args.vcport)
    set_storage_impl(LevelDBStorage("./leveldb"))
    set_vc_client(client)
    app.run(debug=False, host=args.server, port=args.port)