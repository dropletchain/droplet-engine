import leveldb

from checks import *
from chunkdata import CloudChunk
from talosstorage.util import *


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
    def check_chunk_valid(self, chunk, policy, chunk_id=None, time_keeper=TimeKeeper()):
        time_keeper.start_clock()
        if not chunk_id is None:
            if not check_key_matches(chunk, policy, chunk_id):
                raise InvalidChunkError("Chunk key doesn't match")
        time_keeper.stop_clock(ENTRY_PUT_CHECK_CHUNK_KEY_MATCH)

        time_keeper.start_clock()
        if not check_tag_matches(chunk, policy):
            raise InvalidChunkError("Chunk Tag is invalid")
        time_keeper.stop_clock(ENTRY_PUT_CHECK_CHUNK_TAG_MATCH)

        time_keeper.start_clock()
        try:
            check_signature(chunk, policy)
        except InvalidSignature:
            raise InvalidChunkError("Chunk key doesn't match")
        time_keeper.stop_clock(ENTRY_PUT_CHECK_CHUNK_SIGNATURE)

    def check_access_valid(self, pubkey, policy):
        if not check_access_allowed(pubkey, policy):
            raise InvalidAccess("Pubkey not in policy")

    def store_check_chunk(self, chunk, chunk_id, policy, time_keeper=TimeKeeper()):
        time_keeper.start_clock()
        self.check_chunk_valid(chunk, policy, chunk_id=chunk_id, time_keeper=time_keeper)
        time_keeper.stop_clock(ENTRY_PUT_CHECK_CHUNK)

        time_keeper.start_clock()
        result_store = self._store_chunk(chunk)
        time_keeper.stop_clock(ENTRY_PUT_DB)
        return result_store

    def get_check_chunk(self, chunk_key, pubkey, policy, time_keeper=TimeKeeper()):
        time_keeper.start_clock()
        self.check_access_valid(pubkey, policy)
        time_keeper.stop_clock(ENTRY_GET_CHECK_ACCESS)

        time_keeper.start_clock()
        chunk = self._get_chunk(chunk_key)
        time_keeper.stop_clock(ENTRY_GET_DB)

        time_keeper.start_clock()
        if not check_tag_matches(chunk, policy):
            raise InvalidAccess("Chunk not matches policy")
        time_keeper.stop_clock(ENTRY_GET_TAG_CHECK)
        return chunk

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
        bin_chunk = self.db.Get(chunk_key)
        if bin_chunk is None:
            return None
        return CloudChunk.decode(chunk_key + bin_chunk)
