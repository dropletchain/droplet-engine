import unittest
import time
from binascii import hexlify
from cryptography.exceptions import InvalidSignature, InvalidTag

from global_tests.test_storage_api import generate_random_chunk
from talosstorage.checks import check_key_matches, check_tag_matches, check_signature, \
    get_crypto_ecdsa_pubkey_from_bitcoin_hex
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





