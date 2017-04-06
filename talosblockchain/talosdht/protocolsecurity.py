import time
import binascii
import hashlib
import os

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicNumbers

CURVE = ec.SECP192R1
BACKEND = default_backend()


def pub_to_id(pub):
    return hashlib.sha256(pub).digest()[:20]


def pub_to_node_id(public_key):
    return pub_to_id(serialize_pub_key(public_key))


def generate_secret_key():
    return ec.generate_private_key(CURVE, BACKEND)


def check_cbits(node_id, cbits):
    data_long = node_id
    if type(node_id) != long:
        data_long = long(binascii.hexlify(node_id), 16)
    total_bits = len(node_id) * 8
    return (data_long >> (total_bits-cbits)) == 0


def generate_keys_with_crypto_puzzle(c_bits):
    while True:
        private_key = generate_secret_key()
        ser_pub = serialize_pub_key(private_key.public_key())
        node_id = pub_to_id(ser_pub)
        if check_cbits(pub_to_id(node_id), c_bits):
            return private_key, node_id


def generate_token_with_puzzle(node_id, c2_bits):
    while True:
        node_id_b = bytearray(node_id)
        token = bytearray(os.urandom(len(node_id)))
        xor_token = bytes([x ^ y for (x,y) in zip(token, node_id_b)])
        if check_cbits(pub_to_id(xor_token), c2_bits):
            return bytes(token)


def sign_msg(my_ip, my_port, priv_key):
    timestamp = int(time.time())
    data = my_ip + str(my_port) + str(timestamp)
    signer = priv_key.signer(ec.ECDSA(hashes.SHA256()))
    signer.update(data)
    return signer.finalize(), timestamp


def sign_nonce_msg(my_ip, my_port, nonce, priv_key):
    data = my_ip + str(my_port) + nonce
    signer = priv_key.signer(ec.ECDSA(hashes.SHA256()))
    signer.update(data)
    return signer.finalize()


def serialize_pub_key(public_key):
    numbers = public_key.public_numbers()
    return numbers.encode_point()


def deserialize_pub_key(public_key_ser):
    numbers = EllipticCurvePublicNumbers.from_encoded_point(CURVE(), public_key_ser)
    return numbers.public_key(backend=BACKEND)


def serialize_priv_key(private_key):
    numbers = private_key.private_numbers()
    return '%x' % numbers.private_value


def deserialize_priv_key(private_key_hex):
    private_value = long(str(private_key_hex), 16)
    return ec.derive_private_key(private_value, CURVE(), BACKEND)


def check_msg(ip, port, time, signature, pub_key):
    try:
        data = ip + str(port) + str(int(time))
        verifier = pub_key.verifier(signature, ec.ECDSA(hashes.SHA256()))
        verifier.update(data)
        return verifier.verify()
    except InvalidSignature:
        return False


def check_nonce_msg(ip, port, nonce, signature, pub_key):
    try:
        data = ip + str(port) + nonce
        verifier = pub_key.verifier(signature, ec.ECDSA(hashes.SHA256()))
        verifier.update(data)
        return verifier.verify()
    except InvalidSignature:
        return False


def check_time(time_msg, timeout=5):
    return int(time.time()) - time_msg < timeout


def check_pubkey(node_id, pub_key):
    return node_id == pub_to_id(pub_key)