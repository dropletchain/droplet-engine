import json
from threading import Timer

from flask import Flask
from flask import request, g

from talosvc.config import get_working_db, get_default_talos_config
from talosvc.policydb import TalosPolicyDB
from talosvc.talosvirtualchain import sync_blockchain

"""
Implements a REST Api for the talos virtualchain
"""

SYNC_INTERVAL = 60

RUNNING = True

conf = get_default_talos_config()

app = Flask("Talos-Virtualchain")


def set_sync_interval(interval):
    global SYNC_INTERVAL
    SYNC_INTERVAL = interval


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
    global RUNNING
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
            return json.dumps({'owners': [x[0] for x in res]})
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
            return json.dumps({'stream-ids': [x[0] for x in res]})
    except RuntimeError:
        return "ERROR", 400
