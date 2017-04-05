import unittest
from Crypto.Cipher import AES
from ecdsa import BadSignatureError

import ecdsa
import hashlib

class TestStorageApi(unittest.TestCase):

    def test_ecdsa(self):
        ecdsa.SigningKey.from_pem(hashfunc=hashlib.sha256)
        data = "To be signed"
        ecdsa.SigningKey.from_string(

        )
        key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        signature = key.sign(data, hashfunc=hashlib.sha256)
        key_pub = key.get_verifying_key()
        try:
            print key_pub.verify(signature, data + "bad", hashfunc=hashlib.sha256)
        except BadSignatureError:
            print "Invalid Signature"