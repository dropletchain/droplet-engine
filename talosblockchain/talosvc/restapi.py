from flask import Flask
from flask import request, g
from threading import Timer

from talosvc.policydb import TalosPolicyDB
from talosvc.talosvirtualchain import sync_blockchain
from bitcoinrpc.authproxy import AuthServiceProxy


SYNC_INTERVAL = 60

app = Flask("Talos-Virtualchain")


def get_state():
    state = getattr(g, '_state', None)
    if state is None:
        state = g._state = TalosPolicyDB("./test/talos-virtualchain.db")
    return state


def sync_state():
    print "sync"
    app.logger.info('Sync Virtualchain')
    conf = {"bitcoind_port": 18332,
            "bitcoind_user": "talos",
            "bitcoind_passwd": "talos",
            "bitcoind_server": "127.0.0.1",
            "bitcoind_p2p_port": 18444,
            "bitcoind_spv_path": "./tmp.dat"}
    sync_blockchain(conf)
    Timer(SYNC_INTERVAL, sync_state, ()).start()

@app.before_first_request
def initialize():
    Timer(SYNC_INTERVAL, sync_state, ()).start()

@app.teardown_appcontext
def close_connection(exception):
    state = getattr(g, '_state', None)
    if state is not None:
        state.close()

"""
API:
/get_policy?owner=<some_value>&stream-id=<some-value>
"""
@app.route('/policy', methods=['GET'])
def get_policy():
    owner = request.args.get('owner')
    stream_id = request.args.get('stream-id')

    if owner is None or stream_id is None:
        return "ERROR", 400

    vc_state = get_state()

    try:
        res = vc_state.get_policy(owner, int(stream_id))
        if res is None:
            return "NO RESULT FOUND", 400
        else:
            return res.to_json()
    except RuntimeError:
        return "ERROR", 400

app.run(debug=True)


