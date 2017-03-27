from cryptography.exceptions import InvalidSignature

from chunkdata import *
from pybitcoin import BitcoinPublicKey, BitcoinPrivateKey
import os
import base64
import time

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from pybitcoin import BitcoinPublicKey

"""
This file implements the checks of the blocks
Given a Block and a corresponding virtualchain policy perform various checks.
"""

USED_VERSIONBYTE = 111

if 'TALOS_MAINNET' in os.environ and os.environ['TALOS_MAINNET'] == "1":
    USED_VERSIONBYTE = 0
else:
    USED_VERSIONBYTE = 111


class BitcoinVersionedPublicKey(BitcoinPublicKey):
    _version_byte = USED_VERSIONBYTE
    _pubkeyhash_version_byte = USED_VERSIONBYTE


class BitcoinVersionedPrivateKey(BitcoinPrivateKey):
    _version_byte = USED_VERSIONBYTE
    _pubkeyhash_version_byte = USED_VERSIONBYTE


def get_crypto_ecdsa_pubkey_from_bitcoin_hex(bitcoin_hex_key):
    pub = BitcoinVersionedPublicKey(str(bitcoin_hex_key))
    return serialization.load_pem_public_key(pub.to_pem(), backend=default_backend())


def get_bitcoin_address_for_pubkey(hex_pubkey):
    pub = BitcoinVersionedPublicKey(str(hex_pubkey))
    return pub.address()


def get_stream_identifier_from_policy(policy):
    return DataStreamIdentifier(policy.owner, policy.stream_id, policy.get_nonce_bin(), policy.txid)


def check_key_matches(cloud_chunk, policy, chunkid):
    stream_ident = get_stream_identifier_from_policy(policy)
    return cloud_chunk.key == stream_ident.get_key_for_blockid(chunkid)


def check_tag_matches(cloud_chunk, policy):
    stream_ident = get_stream_identifier_from_policy(policy)
    return cloud_chunk.policy_tag == stream_ident.get_tag()


def check_signature(cloud_chunk, policy):
    pub_key = get_crypto_ecdsa_pubkey_from_bitcoin_hex(str(policy.owner_pk))
    return cloud_chunk.check_signature(pub_key)


def check_access_allowed(hex_pubkey, policy):
    addr = get_bitcoin_address_for_pubkey(str(hex_pubkey))
    if addr == policy.owner:
        return True
    if addr in policy.shares:
        return True
    return False


def check_access_key_valid(access_key, policy, blockid):
    stream_ident = get_stream_identifier_from_policy(policy)
    return access_key == stream_ident.get_key_for_blockid(blockid)


def check_pubkey_valid(data, signature, pubkey):
    pub = BitcoinVersionedPublicKey(str(pubkey))
    pub_key = serialization.load_pem_public_key(pub.to_pem(), backend=default_backend())
    try:
        check_signed_data(pub_key, signature, data)
    except InvalidSignature:
        return False
    return True


JSON_TIMESTAMP = "unix_timestamp"
JSON_OWNER = "owner"
JSON_STREAM_ID = "stream_id"
JSON_CHUNK_IDENT = "chunk_key"
JSON_SIGNATURE = "signature"
JSON_PUB_KEY = "pubkey"


def check_valid(json_msg, max_time):
    data = str(json_msg[JSON_TIMESTAMP]) + base64.b64decode(json_msg[JSON_CHUNK_IDENT])
    signature = base64.b64decode(json_msg[JSON_SIGNATURE])
    if not check_pubkey_valid(data, signature, json_msg[JSON_PUB_KEY]):
        return False
    if int(time.time()) - int(json_msg[JSON_TIMESTAMP]) > max_time:
        return False
    return True


def check_json_query_token_valid(json_msg):
    return JSON_TIMESTAMP in json_msg \
           and JSON_CHUNK_IDENT in json_msg \
           and JSON_SIGNATURE in json_msg \
           and JSON_PUB_KEY in json_msg


def get_priv_key(bvpk_private_key):
    return serialization.load_pem_private_key(
        bvpk_private_key.to_pem(),
    password = None,
    backend = default_backend())


def generate_json_query_token(chunk_key, bvpk_private_key):
    private_key = get_priv_key(bvpk_private_key)
    timestamp = int(time.time())
    signature = hash_sign_data(private_key, str(timestamp) + chunk_key)
    return {
        JSON_TIMESTAMP: timestamp,
        JSON_CHUNK_IDENT: base64.b64encode(chunk_key),
        JSON_SIGNATURE:  base64.b64encode(signature),
        JSON_PUB_KEY: bvpk_private_key.to_hex()
    }


class InvalidQueryToken(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def check_query_token_valid(query_token, max_time):
    if query_token is None:
        raise InvalidQueryToken("ERROR No signature supplied")
    if not check_json_query_token_valid(query_token):
        raise InvalidQueryToken("ERROR Invalid JSON token")
    if not check_valid(query_token, max_time):
        raise InvalidQueryToken("ERROR pulibc key not valid")
    return True
