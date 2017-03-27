from talosstorage.storage import TalosStorage
from kademlia.storage import IStorage

class TalosDHTStorage(TalosStorage, IStorage):

    def iteritemsOlderThan(secondsOld):
        super(TalosDHTStorage, secondsOld).iteritemsOlderThan()

    def _store_chunk(self, chunk):
        super(TalosDHTStorage, self)._store_chunk(chunk)

    def iteritems(self):
        super(TalosDHTStorage, self).iteritems()

    def _get_chunk(self, chunk_key):
        super(TalosDHTStorage, self)._get_chunk(chunk_key)

    def __getitem__(key):
        super(TalosDHTStorage, key).__getitem__()

    def __setitem__(key, value):
        super(TalosDHTStorage, key).__setitem__(value)

    def get(key, default=None):
        super(TalosDHTStorage, key).get(default)