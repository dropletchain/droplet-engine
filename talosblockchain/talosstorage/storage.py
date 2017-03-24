from cryptography.exceptions import InvalidSignature
import leveldb

from checks import *


class InvalidChunkError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class InvalidAccess(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class TalosStorage(object):
    def check_chunk_valid(self, chunk, chunk_id, policy):
        if not check_key_matches(chunk, policy, chunk_id):
            raise InvalidChunkError("Chunk key doesn't match")

        if not check_tag_matches(chunk, policy):
            raise InvalidChunkError("Chunk Tag is invalid")
        try:
            check_signature(chunk, policy)
        except InvalidSignature:
            raise InvalidChunkError("Chunk key doesn't match")

    def check_access_valid(self, chunk_key, chunk_id, pubkey, policy):
        if not check_access_key_valid(chunk_key, policy, chunk_id):
            raise InvalidAccess("Chunk key doesnt match policy")
        if not check_access_allowed(pubkey, policy):
            raise InvalidAccess("Pubkey not in policy")

    def store_check_chunk(self, chunk, chunk_id, policy):
        self.check_chunk_valid(chunk, chunk_id, policy)
        return self._store_chunk(chunk)

    def get_check_chunk(self, chunk_key, chunk_id, pubkey, policy):
        self.check_access_valid(chunk_key, chunk_id, pubkey, policy)
        return self._get_chunk(chunk_key)

    def _store_chunk(self, chunk):
        pass

    def _get_chunk(self, chunk_key):
        pass


class LevelDBStorage(TalosStorage):
    def __init__(self, db_dir):
        self.db = leveldb.LevelDB(db_dir)

    def _store_chunk(self, chunk):
        self.db.Put(chunk.key, chunk.get_encoded_without_key())

    def _get_chunk(self, chunk_key):
        return self.db.Get(chunk_key)
