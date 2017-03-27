import base64

from flask import Flask
from flask import request, g
from talosstorage.storage import InvalidChunkError, InvalidAccess, InvalidQueryToken
from talosstorage.checks import JSON_CHUNK_IDENT, check_query_token_valid
from talosstorage.chunkdata import CloudChunk

from talosvc.talosclient.restapiclient import TalosVCRestClient

app = Flask("Talos-Storage-LevelDB")

MAX_TIME = 10

client = TalosVCRestClient()

storage_impl = None


def set_storage_impl(impl):
    global storage_impl
    storage_impl = impl


def set_vc_client(vc_client):
    global client
    client = vc_client


def get_storage():
    state = getattr(g, '_storage', None)
    if state is None:
        state = g._storage = storage_impl
    return state


def get_policy(owner, streamid):
    return client.get_policy(owner, streamid)


def get_policy_with_txid(txid):
    return client.get_policy_with_txid(txid)


"""
Post:
{
"unix_timestamp": "x",
"chunk_key" : "base64(asdadsda)",
"signature" : "base64(H(timestamp | chunk_key) signature)"
"pubkey" : "hex public key"
}
"""
@app.route('/get_chunk/<owner>/<int:streamid>/<int:chunkid>/<hex_pub>', methods=['POST'])
def get_chunk(owner, streamid, chunkid, hex_pub):
    msg = request.get_json(force=True)
    try:
        check_query_token_valid(msg, MAX_TIME)
        if owner is None or streamid is None or chunkid is None:
            return "ERROR Invalid Resource", 400
        chunk_key = base64.b64decode(msg[JSON_CHUNK_IDENT])
        policy = get_policy(owner, streamid)
        storage = get_storage()
        chunk = storage.get_check_chunk(chunk_key, chunkid, hex_pub, policy)
        return chunk.encode()
    except InvalidAccess:
        return "ERROR Invalid access", 400
    except InvalidQueryToken as e:
        return e.value, 400
    except:
        return "ERROR", 400


"""
Post:
bin_block
"""
@app.route('/store_chunk/<int:chunkid>', methods=['POST'])
def store_chunk(chunkid):
    encoded_chunk = request.get_data()
    try:
        chunk = CloudChunk.decode(encoded_chunk)
        policy = get_policy_with_txid(chunk.get_tag_hex())
        storage = get_storage()
        storage.store_check_chunk(chunk, chunkid, policy)
        return "OK", 200
    except InvalidChunkError:
        return "ERROR Invalid chunk", 400

