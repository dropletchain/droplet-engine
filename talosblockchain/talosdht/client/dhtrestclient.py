import binascii

import requests

from talosstorage.checks import generate_query_token
from talosstorage.chunkdata import DataStreamIdentifier, CloudChunk
from talosstorage.timebench import TimeKeeper

TIME_FETCH_ADDRESS = "time_fetch_addr"
TIME_FETCH_NONCE = "time_fetch_nonce"
TIME_FETCH_CHUNK = "time_fetch_chunk"

TIME_STORE_CHUNK = "time_store_chunk"


def store_chunk(session, chunk, ip, port):
    req = session.post("http://%s:%d/store_chunk" % (ip, port), data=chunk.encode())
    return req.reason, req.status_code, req.text


def get_nonce_peer(session, ip, port):
    url = "http://%s:%d/get_chunk" % (ip, port)
    req = session.get(url)
    return req.reason, req.status_code, req.content


def get_chunk_peer(session, json_token, ip, port):
    url = "http://%s:%d/get_chunk" % (ip, port)
    req = session.post(url, json=json_token)
    return req.reason, req.status_code, req.content


def get_chunk_addr(session, chunk_key, ip, port):
    url = "http://%s:%d/chunk_address/%s" % (ip, port, binascii.hexlify(chunk_key))
    req = session.get(url)
    return req.reason, req.status_code, req.text


def get_stream_identifier(owner, stream_id, nonce_policy, txid):
    return DataStreamIdentifier(owner, stream_id, nonce_policy, txid)


def generate_token(block_id, private_key, stream_ident, nonce):
    return generate_query_token(stream_ident.owner, stream_ident.streamid, nonce,
                                stream_ident.get_key_for_blockid(block_id), private_key)


class DHTRestClientException(Exception):
    def __init__(self, description, code, reason, txt):
        self.code = code
        self.reason = reason
        self.txt = txt
        self.description = description

    def __str__(self):
        return "%s Code: %d Reason: %s Response: %s" % (self.description, self.code, repr(self.reason), repr(self.txt))


class DHTRestClient(object):
    def __init__(self, dhtip='127.0.0.1', dhtport=14000):
        self.session = requests.session()
        self.dhtip = dhtip
        self.dhtport = dhtport

    def store_chunk(self, chunk, time_keeper=TimeKeeper()):
        time_keeper.start_clock()
        reason, code, text = store_chunk(self.session, chunk, self.dhtip, self.dhtport)
        time_keeper.stop_clock(TIME_STORE_CHUNK)
        if code == 200:
            return True
        else:
            raise DHTRestClientException("Store chunk error", code, reason, text)

    def fetch_chunk(self, block_id, private_key, stream_identifier, time_keeper=TimeKeeper()):
        time_keeper.start_clock()
        reason, code, address = get_chunk_addr(self.session, stream_identifier.get_key_for_blockid(block_id),
                                               self.dhtip, self.dhtport)
        time_keeper.stop_clock(TIME_FETCH_ADDRESS)

        if code != 200:
            raise DHTRestClientException("Fetch chunk location error", code, reason, address)

        [ip, port] = address.split(':')
        time_keeper.start_clock()
        reason, code, nonce = get_nonce_peer(self.session, ip, int(port))
        time_keeper.stop_clock(TIME_FETCH_NONCE)

        if code != 200:
            raise DHTRestClientException("Fetch nonce error", code, reason, nonce)

        nonce = str(nonce)
        token = generate_token(block_id, private_key, stream_identifier, nonce)

        time_keeper.start_clock()
        reason, code, chunk = get_chunk_peer(self.session, token.to_json(), ip, int(port))
        time_keeper.stop_clock(TIME_FETCH_CHUNK)

        if code != 200:
            raise DHTRestClientException("Fetch chunk error", code, reason, chunk)

        return CloudChunk.decode(chunk)
