import unittest
import time

from talosstorage.chunk import *


class TestChunk(unittest.TestCase):
    def test_chunk1(self):
        chunk = Chunk()
        for i in range(1000):
            entry = DoubleEntry(int(time.time()), "test", float(i))
            chunk.add_entry(entry)
        key = os.urandom(32)
        private_key = ec.generate_private_key(ec.SECP256K1, default_backend())

        compressed_chunk = compress_data(chunk.encode())
        encypted_data = encrypt_aes_gcm_data(key, compressed_chunk)
        signed_data = hash_sign_data(private_key, encypted_data)

        encypted_data_after, ok = check_and_unpack_hash_sign_data(private_key.public_key(), signed_data)
        print ok
        compressed_chunk_after = decrypt_aes_gcm_data(key, encypted_data_after)
        chunk_after = Chunk.decode(decompress_data(compressed_chunk_after))
        print "len compressed len normal %d, %d" % (len(signed_data), len(chunk.encode()))
        for index in range(len(chunk_after.entries)):
            self.assertEquals(str(chunk_after.entries[index]), str(chunk.entries[index]))


