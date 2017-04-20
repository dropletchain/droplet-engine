import base64
import os

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicNumbers
from pybitcoin import BitcoinPrivateKey, extract_bin_ecdsa_pubkey, extract_bin_bitcoin_pubkey, get_bin_hash160, \
    bin_hash160_to_address
from pybitcoin import BitcoinPublicKey

from chunkdata import *

"""
This file implements the checks of the chunks
Given a chunk and the corresponding virtualchain policy perform various checks.
"""


USED_VERSIONBYTE = 111

# Bitcoin keys have different version bytes depending if the testnet or the real network is used
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
    """
    Given a py
    :param bitcoin_hex_key: 
    :return: 
    """
    bin_ecdsa_public_key = extract_bin_ecdsa_pubkey(bitcoin_hex_key)
    numbers = EllipticCurvePublicNumbers.from_encoded_point(ec.SECP256K1(), b'\x04' + bin_ecdsa_public_key)
    return numbers.public_key(backend=default_backend())


def get_bitcoin_address_for_pubkey(hex_pubkey):
    priv = extract_bin_bitcoin_pubkey(hex_pubkey)
    hash_priv = get_bin_hash160(priv)
    return bin_hash160_to_address(hash_priv, version_byte=USED_VERSIONBYTE)


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
    pub_key = get_crypto_ecdsa_pubkey_from_bitcoin_hex(pubkey)
    try:
        check_signed_data(pub_key, signature, data)
    except InvalidSignature:
        return False
    return True


JSON_NONCE = "nonce"
JSON_OWNER = "owner"
JSON_STREAM_ID = "stream_id"
JSON_CHUNK_IDENT = "chunk_key"
JSON_SIGNATURE = "signature"
JSON_PUB_KEY = "pubkey"


class QueryToken(object):
    def __init__(self, owner, streamid, nonce, chunk_key, signature, pubkey):
        self.owner = owner
        self.streamid = streamid
        self.nonce = nonce
        self.chunk_key = chunk_key
        self.signature = signature
        self.pubkey = pubkey

    def get_signature_data(self):
        return str(self.owner) + \
               str(self.streamid) + \
               str(self.nonce) + \
               self.chunk_key

    def to_json(self):
        return {
            JSON_OWNER: self.owner,
            JSON_STREAM_ID: self.streamid,
            JSON_NONCE: base64.b64encode(self.nonce),
            JSON_CHUNK_IDENT: base64.b64encode(self.chunk_key),
            JSON_SIGNATURE: base64.b64encode(self.signature),
            JSON_PUB_KEY: self.pubkey
        }

    @staticmethod
    def from_json(json_msg):
        owner = str(json_msg[JSON_OWNER])
        streamid = int(json_msg[JSON_STREAM_ID])
        nonce = base64.b64decode(json_msg[JSON_NONCE])
        chunk_key = base64.b64decode(json_msg[JSON_CHUNK_IDENT])
        signature = base64.b64decode(json_msg[JSON_SIGNATURE])
        pubkey = str(json_msg[JSON_PUB_KEY])
        return QueryToken(owner, streamid, nonce, chunk_key, signature, pubkey)


def check_valid(token):
    data = token.get_signature_data()
    if not check_pubkey_valid(data, token.signature, token.pubkey):
        return False
    # if int(time.time()) - int(token.timestamp) > max_time:
    #    return False
    return True


def check_json_query_token_valid(json_msg):
    return JSON_OWNER in json_msg \
           and JSON_STREAM_ID in json_msg \
           and JSON_NONCE in json_msg \
           and JSON_CHUNK_IDENT in json_msg \
           and JSON_SIGNATURE in json_msg \
           and JSON_PUB_KEY in json_msg


def get_priv_key(bvpk_private_key):
    private_value = long(bvpk_private_key.to_hex()[:-2], 16)
    return ec.derive_private_key(private_value, ec.SECP256K1(), default_backend())


def generate_query_token(owner, streamid, nonce, chunk_key, bvpk_private_key):
    private_key = get_priv_key(bvpk_private_key)
    data = owner + str(streamid) + str(nonce) + chunk_key
    signature = hash_sign_data(private_key, data)
    return QueryToken(owner, streamid, nonce, chunk_key, signature, bvpk_private_key.public_key().to_hex())


class InvalidQueryToken(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def get_and_check_query_token(json_token):
    if json_token is None:
        raise InvalidQueryToken("ERROR No signature supplied")
    if not check_json_query_token_valid(json_token):
        raise InvalidQueryToken("ERROR Invalid JSON token")
    return QueryToken.from_json(json_token)


def check_query_token_valid(query_token):
    if not check_valid(query_token):
        raise InvalidQueryToken("ERROR pulibc key not valid")
    return True
