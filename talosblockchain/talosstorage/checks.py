#© 2017-2020, ETH Zurich, D-INFK, lubu@inf.ethz.ch

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
    Given a bitcoin hex string key returns the corresponding cryptography ECDSA key object
    :param bitcoin_hex_key: the h
    :return: cryptography ECDSA key object
    """
    bin_ecdsa_public_key = extract_bin_ecdsa_pubkey(bitcoin_hex_key)
    numbers = EllipticCurvePublicNumbers.from_encoded_point(ec.SECP256K1(), b'\x04' + bin_ecdsa_public_key)
    return numbers.public_key(backend=default_backend())


def get_bitcoin_address_for_pubkey(hex_pubkey):
    """
    Computes the bitcoin address given a bitcoin public key in hex format 
    :param hex_pubkey: the bitcoin public key in hex format
    :return: bitcoin address hex string
    """
    priv = extract_bin_bitcoin_pubkey(hex_pubkey)
    hash_priv = get_bin_hash160(priv)
    return bin_hash160_to_address(hash_priv, version_byte=USED_VERSIONBYTE)


def get_stream_identifier_from_policy(policy):
    """
    Given a policy, extracts a StreamIdentifier object
    :param policy: a Talos policy object
    :return: a StreamIdentifier object
    """
    return DataStreamIdentifier(policy.owner, policy.stream_id, policy.get_nonce_bin(), policy.txid)


def check_key_matches(cloud_chunk, policy, chunkid):
    """
    Ficen a cloud chunk object and a policy with the chunkdi checks if the key matches
    :param cloud_chunk: a cloud chunk object
    :param policy: a policy object
    :param chunkid: (int) chunk identifier 
    :return: True if ok else False
    """
    stream_ident = get_stream_identifier_from_policy(policy)
    return cloud_chunk.key == stream_ident.get_key_for_blockid(chunkid)


def check_tag_matches(cloud_chunk, policy):
    """
    Given a cloud chunk and a policy, checks if the chunk is linke to the policy with the 
    tag
    :param cloud_chunk: a cloud chunk object
    :param policy: a policy object
    :return: True if ok else False
    """
    stream_ident = get_stream_identifier_from_policy(policy)
    return cloud_chunk.policy_tag == stream_ident.get_tag()


def check_signature(cloud_chunk, policy):
    """
    Given a cloud chunk and a policy, checks if the cloud chunk has a valid signature 
    :param cloud_chunk: a cloud chunk object
    :param policy: a policy object
    :return: True if ok else False
    """
    pub_key = get_crypto_ecdsa_pubkey_from_bitcoin_hex(str(policy.owner_pk))
    return cloud_chunk.check_signature(pub_key)


def check_access_allowed(hex_pubkey, policy):
    """
    Given a bicoin hex string public key and a policy, checks if the public key is 
    the owner or in the shares list
    :param hex_pubkey: the bitcoin hex string key
    :param policy: a policy object
    :return: True if owner or in shares else False
    """
    addr = get_bitcoin_address_for_pubkey(str(hex_pubkey))
    if addr == policy.owner:
        return True
    if policy.check_has_share(addr):
        return True
    return False


def check_access_key_valid(access_key, policy, blockid):
    """
    Chekcs if the access key matches the policy and the chunk identifier.
    :param access_key: hex key
    :param policy: the policy
    :param blockid: the id of the chunk
    :return: Ture if ok else False
    """
    stream_ident = get_stream_identifier_from_policy(policy)
    return access_key == stream_ident.get_key_for_blockid(blockid)


def check_pubkey_valid(data, signature, pubkey):
    """
    Checks if the data has a valid signature with the given public key.
    :param data: the data
    :param signature: the signature
    :param pubkey: the bitcoin public key as a hex string
    :return: 
    """
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
    """
    Represents a token for retrieving a specific chunk. 
    Contains an owner, the stream id, a nonce, the chunk retrival key, a signature and 
    the the public key.
    """
    def __init__(self, owner, streamid, nonce, chunk_key, signature, pubkey):
        """
        Inits a query token
        :param owner: the bitcoin address of the stream owner
        :param streamid: the stream identifier (int)
        :param nonce: a challenge nonce against replays 
        :param chunk_key: the chunk key for retreiving the chunk from the storage
        :param signature: a signature of the token
        :param pubkey: the public key hey string of the signature
        """
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
    """
    Given a query token checks if the token is valid. (Signature check)
    :param token: the QueryToken object
    :return: True if ok else False
    """
    data = token.get_signature_data()
    if not check_pubkey_valid(data, token.signature, token.pubkey):
        return False
    # if int(time.time()) - int(token.timestamp) > max_time:
    #    return False
    return True


def check_json_query_token_valid(json_msg):
    """
    Checks if a json msg contains all query token json fields
    :param json_msg: the json message as map
    :return: True if ok else False
    """
    return JSON_OWNER in json_msg \
           and JSON_STREAM_ID in json_msg \
           and JSON_NONCE in json_msg \
           and JSON_CHUNK_IDENT in json_msg \
           and JSON_SIGNATURE in json_msg \
           and JSON_PUB_KEY in json_msg


def get_priv_key(bvpk_private_key):
    """
    Given a pybitcoin private key computes the corresponding cryptography private key object.
    :param bvpk_private_key: a pybitcoin private key
    :return: cryptography ECDSA private key object
    """
    private_value = long(bvpk_private_key.to_hex()[:-2], 16)
    return ec.derive_private_key(private_value, ec.SECP256K1(), default_backend())


def generate_query_token(owner, streamid, nonce, chunk_key, bvpk_private_key):
    """
    Generates a QueryToken object given the owner, stream_id, nonce, chunk retrival key and 
    a pybitcoin private key object
    :param owner: the bitcoin addres of the stream ownder (hex string)
    :param streamid: the stream id (int)
    :param nonce: the challange nonce
    :param chunk_key: the chunk retrival key
    :param bvpk_private_key: a BitcoinVersionedPrivateKey object
    :return: a QueryToken object
    """
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
    """
    Given a json query token as map, returns the QueryToken object.
    :param json_token: the json msg as map
    :return: a QueryToken objec if ok t, else throws InvalidQueryToken exception
    """
    if json_token is None:
        raise InvalidQueryToken("ERROR No signature supplied")
    if not check_json_query_token_valid(json_token):
        raise InvalidQueryToken("ERROR Invalid JSON token")
    return QueryToken.from_json(json_token)


def check_query_token_valid(query_token):
    """
    Given a QueryToken object, checks if the token is valid
    :param query_token: the QueryToken object
    :return: True if ok else throws InvalidQueryToken exception
    """
    if not check_valid(query_token):
        raise InvalidQueryToken("ERROR pulibc key not valid")
    return True
