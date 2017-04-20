import struct
import time

from kademlia.storage import IStorage
from twisted.internet import threads
from zope.interface import implements

from talosstorage.chunkdata import CloudChunk
from talosstorage.storage import LevelDBStorage


def add_time_chunk(encoded_chunk):
    return struct.pack("I", int(time.time())) + encoded_chunk


def get_time_and_chunk(encoded):
    size_time = struct.calcsize("I")
    time_cur, = struct.unpack("I", encoded[:size_time])
    return time_cur, encoded[size_time:]


class TalosLevelDBDHTStorage(LevelDBStorage):
    implements(IStorage)

    def __init__(self, db_dir, time_db_name="dhttimedb"):
        LevelDBStorage.__init__(self, db_dir)

    def iteritemsOlderThan(self, secondsOld):
        cur_time = int(time.time())
        for key, value in self.db.RangeIter():
            time_value, real_value = get_time_and_chunk(value)
            if cur_time - time_value > secondsOld:
                yield key, real_value

    def _store_chunk(self, chunk):
        self.db.Put(chunk.key, add_time_chunk(chunk.encode()))

    def iteritems(self):
        for key, value in self.db.RangeIter():
            _, real_value = get_time_and_chunk(value)
            yield key, real_value

    def __setitem__(self, key, value):
        self._store_chunk(value)

    def __getitem__(self, key):
        self._get_chunk(key)

    def get(self, key, default=None):
        res = self._get_chunk(key)
        return default if res is None else res

    def has_value(self, to_find):
        try:
            self.db.Get(to_find)
            return True
        except KeyError:
            return False

    def _get_chunk(self, chunk_key):
        try:
            encoded = self.db.Get(chunk_key)
        except KeyError:
            return None
        _, bin_chunk = get_time_and_chunk(encoded)

        def store_update():
            self.db.Put(chunk_key, add_time_chunk(bin_chunk))

        threads.deferToThread(store_update)
        return CloudChunk.decode(bin_chunk)
