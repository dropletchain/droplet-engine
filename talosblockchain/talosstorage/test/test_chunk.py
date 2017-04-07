import unittest
import time
from cryptography.exceptions import InvalidSignature, InvalidTag
from cryptography.hazmat.primitives import serialization

from global_tests.test_storage_api import generate_random_chunk
from talosstorage.checks import check_key_matches, check_tag_matches, check_signature, \
    get_crypto_ecdsa_pubkey_from_bitcoin_hex, BitcoinVersionedPrivateKey, get_priv_key
from talosstorage.chunkdata import *

import talosstorage.keymanagement as km
from timeit import default_timer as timer

from talosstorage.storage import InvalidChunkError
from talosvc.talosclient.restapiclient import TalosVCRestClient


class TestChunk(unittest.TestCase):

    def test_chunk1(self):
        chunk = ChunkData()
        for i in range(1000):
            entry = DoubleEntry(int(time.time()), "test", float(i))
            chunk.add_entry(entry)
        key = os.urandom(32)
        private_key = ec.generate_private_key(ec.SECP256K1, default_backend())
        stream_ident = DataStreamIdentifier("pubaddr", 3, "asvcgdterategdts",
                                            "59f7a5a9de7a44ad0f8b0cb95faee0a2a43af1f99ec7cab036b737a4c0f911bb")

        cd = create_cloud_chunk(stream_ident, 1, private_key, 1, key, chunk)
        self.assertTrue(cd.check_signature(private_key.public_key()))
        chunk_after = cd.get_and_check_chunk_data(key)

        for i in range(len(chunk_after.entries)):
            self.assertEquals(str(chunk_after.entries[i]), str(chunk.entries[i]))

        encoded_cloud_chunk = cd.encode()
        cloud_chunk_after = CloudChunk.decode(encoded_cloud_chunk)

        self.assertTrue(cloud_chunk_after.check_signature(private_key.public_key()))
        chunk_after = cd.get_and_check_chunk_data(key)

        for i in range(len(chunk_after.entries)):
            self.assertEquals(str(chunk_after.entries[i]), str(chunk.entries[i]))
        encoded_cloud_chunk = list(encoded_cloud_chunk)
        encoded_cloud_chunk[2] = 'x'
        encoded_cloud_chunk = "".join(encoded_cloud_chunk)
        cloud_chunk_after = CloudChunk.decode(encoded_cloud_chunk)

        ok = False
        try:
            cloud_chunk_after.check_signature(private_key.public_key())
        except InvalidSignature:
            ok = True
        self.assertTrue(ok)

        ok = False
        try:
            cloud_chunk_after.get_and_check_chunk_data(key)
        except InvalidTag:
            ok = True
        self.assertTrue(ok)

    def test_picture_entry(self):
        with open("./pylepton/haas.jpg", 'r') as f:
            pic = f.read()
        chunk = ChunkData(type=TYPE_PICTURE_ENTRY)
        for i in range(5):
            entry = PictureEntry(int(time.time()), "haas.jpg", pic)
            chunk.add_entry(entry)
        encoded = chunk.encode()
        chunk_after = ChunkData.decode(encoded)
        self.assertEquals(pic, chunk_after.entries[0].picture_data)


def check_chunk_valid(chunk, policy, chunk_id=None):
    try:
        check_signature(chunk, policy)
    except InvalidSignature:
        raise InvalidChunkError("Chunk key doesn't match")


class MeasureCheck(unittest.TestCase):
    def test_chunk1(self):
        client = TalosVCRestClient()
        for i in range(100):
            chunk = generate_random_chunk(i)
            policy = client.get_policy_with_txid(chunk.get_tag_hex())
            before = timer()
            check_chunk_valid(chunk, policy, chunk_id=i)
            print "Time check %s" % ((timer()-before)*1000,)

    def test_signature(self):
        data = "Hello"*1000

        prv_key = ec.generate_private_key(ec.SECP256K1, default_backend())

        for i in range(100):
            signature = hash_sign_data(prv_key, data)
            before = timer()
            check_signed_data(prv_key.public_key(), signature, data)
            print "Time check %s" % ((timer() - before) * 1000,)

    def test_cross(self):
        client = TalosVCRestClient()
        for i in range(100):
            chunk = generate_random_chunk(i)
            policy = client.get_policy_with_txid(chunk.get_tag_hex())
            before = timer()
            pub_key = get_crypto_ecdsa_pubkey_from_bitcoin_hex(str(policy.owner_pk))
            print "Time check %s" % ((timer() - before) * 1000,)

    def test_key_siwtch(self):
        key = BitcoinVersionedPrivateKey("cN5YgNRq8rbcJwngdp3fRzv833E7Z74TsF8nB6GhzRg8Gd9aGWH1")

        def get_priv_key2(bvpk_private_key):
            return serialization.load_pem_private_key(
                bvpk_private_key.to_pem(),
                password=None,
                backend=default_backend())

        other = get_priv_key(key)
        priv2 = get_priv_key2(key)

        def serialize_priv_key(private_key):
            numbers = private_key.private_numbers()
            return '%x' % numbers.private_value
        ser_priv1 = serialize_priv_key(other)
        ser_priv2 = serialize_priv_key(priv2)
        print "%s\n%s" % (ser_priv1, ser_priv2)

        self.assertEquals(serialize_priv_key(other), serialize_priv_key(priv2))
        self.assertEquals(other.private_numbers(), priv2.private_numbers())

        data = "Hello"
        signature1 = hash_sign_data(other, data)
        signature2 = hash_sign_data(priv2, data)

        self.assertTrue(check_signed_data(other.public_key(), signature2, data))
        self.assertTrue(check_signed_data(priv2.public_key(), signature1, data))


class TestKeyReg(unittest.TestCase):

    def test_key_reg(self):
        n = 100
        max_version = 500
        gen = km.KeyRegressionGenerator(seed="hello", n=n)
        key_10, seeda = gen.get_key(max_version-1)
        for i in range(max_version):
            compare = km.KeyRegressionPastGenerator(seeda, key_10, max_version-1, n=n)
            key_null, seed = gen.get_key(i)
            compare_key = compare.get_key(i)
            #print "before: %s after: %s" % (hexlify(key_null), hexlify(compare_key))
            self.assertEquals(compare_key, key_null)

    def test_encode_decode(self):
        n = 100
        gen = km.KeyRegressionGenerator(seed="hello", n=n)
        key, seed = gen.get_key(n*2)
        encoded = km.encode_key(n*2, n, key, seed)
        dn, dversion, dkey, dseed = km.decode_key(encoded)
        #print "before: %s after: %s" % (hexlify(seed), hexlify(dseed))
        self.assertEquals(dn, n*2)
        self.assertEquals(dversion, n)
        self.assertEquals(dkey, key)
        self.assertEquals(dseed, seed)





