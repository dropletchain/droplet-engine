import unittest
import time

from cryptography.exceptions import InvalidSignature, InvalidTag

from talosstorage.chunkdata import *


class TestChunk(unittest.TestCase):
    def test_chunk1(self):
        chunk = ChunkData()
        for i in range(1000):
            entry = DoubleEntry(int(time.time()), "test", float(i))
            chunk.add_entry(entry)
        key = os.urandom(32)
        private_key = ec.generate_private_key(ec.SECP256K1, default_backend())
        stream_ident = DataStreamIdentifier("pubaddr", 3, "asvcgdterategdts")

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


