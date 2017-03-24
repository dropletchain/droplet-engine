from cryptography.exceptions import InvalidSignature

from chunkdata import *
from pybitcoin import BitcoinPublicKey
import os

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


def get_crypto_ecdsa_pubkey_from_bitcoin_hex(bitcoin_hex_key):
    pub = BitcoinVersionedPublicKey(bitcoin_hex_key)
    return serialization.load_pem_public_key(pub.to_pem(), backend=default_backend())


def get_bitcoin_address_for_pubkey(hex_pubkey):
    pub = BitcoinVersionedPublicKey(hex_pubkey)
    return pub.address()


def get_stream_identifier_from_policy(policy):
    return DataStreamIdentifier(policy.owner, policy.stream_id, policy.nonce, policy.txid)


def check_key_matches(cloud_chunk, policy, chunkid):
    stream_ident = get_stream_identifier_from_policy(policy)
    return cloud_chunk.key == stream_ident.get_key_for_blockid(chunkid)


def check_tag_matches(cloud_chunk, policy):
    stream_ident = get_stream_identifier_from_policy(policy)
    return cloud_chunk.policy_tag == stream_ident.get_tag()


def check_signature(cloud_chunk, policy):
    pub_key = get_crypto_ecdsa_pubkey_from_bitcoin_hex(policy.owner_pk)
    return cloud_chunk.check_signature(pub_key)


def check_access_allowed(hex_pubkey, policy):
    addr = get_bitcoin_address_for_pubkey(hex_pubkey)
    if addr == policy.owner:
        return True
    if addr in policy.shares:
        return True
    return False


def check_access_key_valid(access_key, policy, blockid):
    stream_ident = get_stream_identifier_from_policy(policy)
    return access_key == stream_ident.get_key_for_blockid(blockid)


def check_pubkey_valid(data, signature, pubkey):
    pub = BitcoinVersionedPublicKey(pubkey)
    pub_key = serialization.load_pem_public_key(pub.to_pem(), backend=default_backend())
    try:
        check_signed_data(pub_key, signature, data)
    except InvalidSignature:
        return False
    return True