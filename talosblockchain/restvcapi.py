import json
import argparse

from flask import Flask
from flask import request, g
from threading import Timer

from talosvc.config import get_working_db, get_default_talos_config
from talosvc.policydb import TalosPolicyDB
from talosvc.talosvirtualchain import sync_blockchain


SYNC_INTERVAL = 60

app = Flask("Talos-Virtualchain")

RUNNING = True

conf = get_default_talos_config()


def get_state():
    state = getattr(g, '_state', None)
    if state is None:
        state = g._state = TalosPolicyDB(get_working_db())
    return state


def sync_state():
    app.logger.info('Sync Virtualchain')
    try:
        sync_blockchain(conf)
    finally:
        if RUNNING:
            Timer(SYNC_INTERVAL, sync_state, ()).start()

@app.before_first_request
def initialize():
    Timer(SYNC_INTERVAL, sync_state, ()).start()

@app.teardown_appcontext
def close_connection(exception):
    state = getattr(g, '_state', None)
    if state is not None:
        state.close()
    RUNNING = False


@app.route('/policy', methods=['GET'])
def get_policy():
    """
    API:
    /get_policy?owner=<some_value>&stream-id=<some-value>
    /get_policy?txid=<some_value>
    """
    owner = request.args.get('owner')
    stream_id = request.args.get('stream-id')
    txid = request.args.get('txid')

    if (owner is None or stream_id is None) and txid is None:
        return "ERROR", 400


    vc_state = get_state()

    try:
        if not txid is None:
            res = vc_state.get_policy_with_txid(txid)
        else:
            res = vc_state.get_policy(owner, int(stream_id))
        if res is None:
            return "NO RESULT FOUND", 400
        else:
            return res.to_json()
    except RuntimeError:
        return "ERROR", 400


@app.route('/owners', methods=['GET'])
def get_owners():
    """
    API:
    /owners?limit=<limit>&offset=<offset>
    """
    limit = request.args.get('limit')
    offset = request.args.get('offset')

    if limit is None:
        limit = 10
    if offset is None:
        offset = 0

    vc_state = get_state()

    try:
        res = vc_state.get_owners(limit, offset)
        if res is None:
            return "NO RESULT FOUND", 400
        else:
            return json.dumps({'owners':[x[0] for x in res]})
    except RuntimeError:
        return "ERROR", 400


@app.route('/streamids', methods=['GET'])
def get_streamids_for_owner():
    """
    API:
    /streamids?owner=<owner>
    """
    owner = request.args.get('owner')

    if owner is None:
        return "ERROR", 400

    vc_state = get_state()

    try:
        res = vc_state.get_policies_for_owner(owner)
        if res is None:
            return "NO RESULT FOUND", 400
        else:
            return json.dumps({'stream-ids':[x[0] for x in res]})
    except RuntimeError:
        return "ERROR", 400


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

    RUNNING = True

    SYNC_INTERVAL = args.sync
    print get_working_db()
    print "Running with conf %s " % conf

    sync_blockchain(conf)
    print "Sync done"
    app.run(debug=False, host='0.0.0.0')




