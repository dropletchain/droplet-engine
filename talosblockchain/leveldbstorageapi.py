import base64
import urllib2

import requests
import argparse

from flask import Flask
from flask import request, g
from talosstorage.storage import LevelDBStorage, InvalidChunkError, InvalidAccess
from talosstorage.checks import check_pubkey_valid
from talosstorage.chunkdata import CloudChunk

from talosvc.policy import create_policy_from_json_str

import time

app = Flask("Talos-Storage-LevelDB")

VC_IP = "127.0.0.1"
VC_PORT = 5000

RUNNING = True

JSON_TIMESTAMP = "unix_timestamp"
JSON_CHUNK_IDENT = "chunk_key"
JSON_SIGNATURE = "signature"
MAX_TIME = 10

def get_storage():
    state = getattr(g, '_storage', None)
    if state is None:
        state = g._storage = LevelDBStorage("./leveldb")
    return state


def check_valid(json_msg, pub_key_hex):
    data = str(json_msg[JSON_TIMESTAMP]) + base64.b64decode(json_msg[JSON_CHUNK_IDENT])
    signature = base64.b64decode(json_msg[JSON_SIGNATURE])
    if not check_pubkey_valid(data, signature, pub_key_hex):
        return False
    if int(time.time()) - int(json_msg[JSON_TIMESTAMP]) > MAX_TIME:
        return False
    return True


def check_json_valid(json_msg):
    return JSON_TIMESTAMP in json_msg \
           and JSON_CHUNK_IDENT in json_msg \
           and JSON_SIGNATURE in json_msg


def get_policy(owner, streamid):
    return create_policy_from_json_str(
        urllib2.urlopen("http://%s:%d/policy?owner=%s&stream-id=%d" % (VC_IP, VC_PORT, owner, streamid)).read())


def get_policy_with_txid(txid):
    req = requests.get("http://%s:%d/policy?txid=%s" % (VC_IP, VC_PORT, txid))
    return create_policy_from_json_str(req.text)

"""
Post:
{
"unix_timestamp": "x",
"chunk_key" : "base64(asdadsda)",
"signature" : "base64(H(timestamp | chunk_key) signature)"
}
"""
@app.route('/get_chunk/<owner>/<int:streamid>/<int:chunkid>/<hex_pub>', methods=['POST'])
def get_chunk(owner, streamid, chunkid, hex_pub):
    msg = request.get_json(force=True)
    try:
        if msg is None:
            return "ERROR No signature supplied", 400
        if not check_json_valid(msg):
            return "ERROR INVALID JSON", 400
        if owner is None or streamid is None or chunkid is None or hex_pub is None:
            return "ERROR Invalid Resource", 400
        if not check_valid(msg, hex_pub):
            return "ERROR pulibc key not valid", 400
        chunk_key = base64.b64decode(msg[JSON_CHUNK_IDENT])
        policy = get_policy(owner, streamid)
        storage = get_storage()
        chunk = storage.get_check_chunk(chunk_key, chunkid, hex_pub, policy)
        return chunk.encode()
    except InvalidAccess:
        return "ERROR Invalid access", 400
    #except:
        #return "ERROR", 400

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
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Run storage server client")
    parser.add_argument('--vcport', type=int, help='dir', default=5000, required=False)
    parser.add_argument('--vcserver', type=str, help='server', default="127.0.0.1", required=False)
    parser.add_argument('--port', type=int, help='dir', default=12000, required=False)
    parser.add_argument('--server', type=str, help='server', default="127.0.0.1", required=False)
    args = parser.parse_args()

    VC_IP = args.vcserver
    VC_PORT = args.vcport

    app.run(debug=False, host=args.server, port=args.port)