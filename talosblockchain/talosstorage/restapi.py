import base64

from flask import Flask
from flask import request, g
from talosstorage.storage import InvalidChunkError, InvalidAccess, InvalidQueryToken
from talosstorage.checks import JSON_CHUNK_IDENT, check_query_token_valid, get_and_check_query_token
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
"owner": "sdfsdf",
"stream_id": "3",
"unix_timestamp": "x",
"chunk_key" : "base64(asdadsda)",
"signature" : "base64(H(owner | str(stream_id) | str(timestamp) | chunk_key) signature)",
"pubkey" : "hex public key"
}
"""
@app.route('/get_chunk', methods=['POST'])
def get_chunk():
    msg = request.get_json(force=True)
    try:
        token = get_and_check_query_token(msg)
        check_query_token_valid(token, MAX_TIME)
        policy = get_policy(token.owner, token.streamid)
        storage = get_storage()
        chunk = storage.get_check_chunk(token.chunk_key, token.pubkey, policy)
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

