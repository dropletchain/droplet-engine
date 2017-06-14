from talosstorage.storage import TalosStorage
import ipfsapi


class IPFSStorage(TalosStorage):

    def __init__(self, ip, port):
        TalosStorage.__init__(self)
        self.ipfs_api = ipfsapi.connect(ip, port)

    def make_dir(self, ownerid):
        d = "/ipfs/%s" % ownerid
        self.ipfs_api.files_mkdir(d, parents=True)


    def _get_chunk(self, chunk_key):
        super(IPFSStorage, self)._get_chunk(chunk_key)

    def _store_chunk(self, chunk):
        super(IPFSStorage, self)._store_chunk(chunk)