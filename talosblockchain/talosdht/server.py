"""
Package for interacting on the network at a high level.
"""
import random
import binascii
import pickle

from twisted.internet.task import LoopingCall
from twisted.internet import defer, reactor, task

from kademlia.log import Logger
from kademlia.utils import deferredDict, digest
from kademlia.node import Node
from kademlia.crawling import NodeSpiderCrawl
from twisted.web.resource import Resource
from twisted.web.server import Site

from talosdht.asyncpolicy import AsyncPolicyApiClient
from talosdht.crawlers import TalosChunkSpiderCrawl
from talosdht.dhtstorage import TalosLevelDBDHTStorage
from talosdht.protocolsecurity import generate_keys_with_crypto_puzzle, pub_to_node_id, serialize_priv_key, \
    deserialize_priv_key
from talosdht.talosprotocol import TalosKademliaProtocol, TalosHTTPClient, QueryChunk, StoreLargeChunk, \
    TalosSKademliaProtocol
from talosstorage.chunkdata import CloudChunk



class TalosDHTServerError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class TalosDHTServer(object):
    """
    Modified implementation of bmullers DHT for talos
    High level view of a node instance.  This is the object that should be created
    to start listening as an active node on the network.
    
    We assume public ip addresses! No NAT etc
    """

    def __init__(self, ksize=20, alpha=3, id=None, storage=None,
                 talos_vc=None, rebub_delay=3600):
        """
        Create a server instance.  This will start listening on the given port.
        Args:
            ksize (int): The k parameter from the paper
            alpha (int): The alpha parameter from the paper
            id: The id for this node on the network.
            storage: An instance that implements :interface:`~kademlia.storage.IStorage`
        """
        self.ksize = ksize
        self.alpha = alpha
        self.log = Logger(system=self)
        self.storage = storage or TalosLevelDBDHTStorage("./leveldb")
        self.node = Node(id or digest(random.getrandbits(255)))

        def start_looping_call(num_seconds):
            self.refreshLoop = LoopingCall(self.refreshTable).start(num_seconds)
        self.delay = rebub_delay
        task.deferLater(reactor, rebub_delay, start_looping_call, rebub_delay)
        self.talos_vc = talos_vc or AsyncPolicyApiClient()
        self.protocol = TalosKademliaProtocol(self.node, self.storage, ksize, talos_vc=self.talos_vc)
        self.httpprotocol_client = None

    def listen(self, port, interface="127.0.0.1"):
        """
        Init tcp/udp protocol on the given port
        Start listening on the given port.
        """
        root = Resource()
        root.putChild("get_chunk", QueryChunk(self.storage, talos_vc=self.talos_vc))
        root.putChild("storelargechunk", StoreLargeChunk(self.storage, self.protocol, talos_vc=self.talos_vc))
        factory = Site(root)

        self.httpprotocol_client = TalosHTTPClient(self.protocol, port)
        self.protocol.http_client = self.httpprotocol_client
        reactor.listenTCP(port, factory, interface=interface)
        return reactor.listenUDP(port, self.protocol, interface, maxPacketSize=65535)

    def refreshTable(self):
        """
        Refresh buckets that haven't had any lookups in the last hour
        (per section 2.3 of the paper).
        """
        self.log.info("Refreshing table")
        ds = []
        for id in self.protocol.getRefreshIDs():
            node = Node(id)
            nearest = self.protocol.router.findNeighbors(node, self.alpha)
            spider = NodeSpiderCrawl(self.protocol, node, nearest, self.ksize, self.alpha)
            ds.append(spider.find())

        def republishKeys(_):
            ds = []
            # Republish keys older than one hour
            for dkey, value in self.storage.iteritemsOlderThan(self.delay):
                ds.append(self.digest_set(digest(dkey), value))
            return defer.gatherResults(ds)

        return defer.gatherResults(ds).addCallback(republishKeys)

    def bootstrappableNeighbors(self):
        """
        Get a :class:`list` of (ip, port) :class:`tuple` pairs suitable for use as an argument
        to the bootstrap method.
        The server should have been bootstrapped
        already - this is just a utility for getting some neighbors and then
        storing them if this server is going down for a while.  When it comes
        back up, the list of nodes can be used to bootstrap.
        """
        neighbors = self.protocol.router.findNeighbors(self.node)
        return [ tuple(n)[-2:] for n in neighbors ]

    def bootstrap(self, addrs):
        """
        Bootstrap the server by connecting to other known nodes in the network.
        Args:
            addrs: A `list` of (ip, port) `tuple` pairs.  Note that only IP addresses
                   are acceptable - hostnames will cause an error.
        """
        # if the transport hasn't been initialized yet, wait a second
        if self.protocol.transport is None:
            return task.deferLater(reactor, 1, self.bootstrap, addrs)

        def initTable(results):
            nodes = []
            for addr, result in results.items():
                if result[0]:
                    nodes.append(Node(result[1], addr[0], addr[1]))
            spider = NodeSpiderCrawl(self.protocol, self.node, nodes, self.ksize, self.alpha)
            return spider.find()

        ds = {}
        for addr in addrs:
            ds[addr] = self.protocol.ping(addr, self.node.id)
        return deferredDict(ds).addCallback(initTable)

    def inetVisibleIP(self):
        """
        Get the internet visible IP's of this node as other nodes see it.
        Returns:
            A `list` of IP's.  If no one can be contacted, then the `list` will be empty.
        """
        def handle(results):
            ips = [ result[1][0] for result in results if result[0] ]
            self.log.debug("other nodes think our ip is %s" % str(ips))
            return ips

        ds = []
        for neighbor in self.bootstrappableNeighbors():
            ds.append(self.protocol.stun(neighbor))
        return defer.gatherResults(ds).addCallback(handle)

    def store_chunk(self, chunk, policy=None):
        dkey = digest(chunk.key)
        self.log.debug("Storing chunk with key %s" % (binascii.hexlify(dkey),))
        return self.digest_set(dkey, chunk.encode(), policy_in=policy)

    def get_addr_chunk(self, chunk_key, policy_in=None):
        # if this node has it, return it
        if self.storage.has_value(chunk_key):
            addr = self.protocol.get_address()
            return defer.succeed("%s:%d" % (addr[0], addr[1]))
        dkey = digest(chunk_key)
        node = Node(dkey)
        nearest = self.protocol.router.findNeighbors(node)
        self.log.debug("Crawling for key %s" % (binascii.hexlify(dkey),))
        if len(nearest) == 0:
            self.log.warning("There are no known neighbors to get key %s" % binascii.hexlify(dkey))
            return defer.succeed(None)
        spider = TalosChunkSpiderCrawl(self.protocol, self.httpprotocol_client, node, chunk_key, nearest, self.ksize, self.alpha)
        return spider.find()

    def digest_set(self, dkey, value, policy_in=None):
        """
        Set the given SHA1 digest key to the given value in the network.
        """
        node = Node(dkey)
        # this is useful for debugging messages
        hkey = binascii.hexlify(dkey)

        def store(nodes):
            self.log.info("setting '%s' on %s" % (hkey, map(str, nodes)))
            # if this node is close too, then store here as well
            if self.node.distanceTo(node) < max([n.distanceTo(node) for n in nodes]):
                chunk = CloudChunk.decode(value)
                if not digest(chunk.key) == dkey:
                    return {'error': 'key missmatch'}

                def handle_policy(policy):
                    # Hack no chunk id given -> no key checks, key is in the encoded chunk
                    self.storage.store_check_chunk(chunk, None, policy)
                    ds = [self.protocol.callStore(n, dkey, value) for n in nodes]
                    return defer.DeferredList(ds).addCallback(self._anyRespondSuccess)

                if not policy_in is None:
                    return handle_policy(policy_in)
                return self.talos_vc.get_policy_with_txid(chunk.get_tag_hex()).addCallback(handle_policy)

            ds = [self.protocol.callStore(n, dkey, value) for n in nodes]
            return defer.DeferredList(ds).addCallback(self._anyRespondSuccess)

        nearest = self.protocol.router.findNeighbors(node)
        if len(nearest) == 0:
            self.log.warning("There are no known neighbors to set key %s" % hkey)
            return defer.succeed(False)
        spider = NodeSpiderCrawl(self.protocol, node, nearest, self.ksize, self.alpha)
        return spider.find().addCallback(store)

    def _anyRespondSuccess(self, responses):
        """
        Given the result of a DeferredList of calls to peers, ensure that at least
        one of them was contacted and responded with a Truthy result.
        """
        for deferSuccess, result in responses:
            peerReached, peerResponse = result
            if deferSuccess and peerReached and peerResponse:
                return True
        return False

    def saveState(self, fname):
        """
        Save the state of this node (the alpha/ksize/id/immediate neighbors)
        to a cache file with the given fname.
        """
        self.log.info("Save state to file %s" % fname)
        data = { 'ksize': self.ksize,
                 'alpha': self.alpha,
                 'id': self.node.id,
                 'neighbors': self.bootstrappableNeighbors() }
        if len(data['neighbors']) == 0:
            self.log.warning("No known neighbors, so not writing to cache.")
            return
        with open(fname, 'w') as f:
            pickle.dump(data, f)

    @classmethod
    def loadState(self, fname, storage=None, talos_vc=None):
        """
        Load the state of this node (the alpha/ksize/id/immediate neighbors)
        from a cache file with the given fname.
        """
        with open(fname, 'r') as f:
            data = pickle.load(f)
        s = TalosDHTServer(data['ksize'], data['alpha'], data['id'], storage=None, talos_vc=None)
        if len(data['neighbors']) > 0:
            s.bootstrap(data['neighbors'])
        return s

    def saveStateRegularly(self, fname, frequency=600):
        """
        Save the state of node with a given regularity to the given
        filename.
        Args:
            fname: File name to save retularly to
            frequencey: Frequency in seconds that the state should be saved.
                        By default, 10 minutes.
        """
        def run_looping_call(freq):
            loop = LoopingCall(self.saveState, fname).start(freq)
            return defer.succeed(loop)
        return task.deferLater(reactor, frequency, run_looping_call, frequency)



class TalosSecureDHTServer(TalosDHTServer):

    def __init__(self, ksize=20, alpha=3, priv_key=None, storage=None,
                 talos_vc=None, rebub_delay=3600, c1bits=10):
        """
        Create a server instance.  This will start listening on the given port.
        Args:
            ksize (int): The k parameter from the paper
            alpha (int): The alpha parameter from the paper
            id: The id for this node on the network.
            storage: An instance that implements :interface:`~kademlia.storage.IStorage`
        """
        self.ksize = ksize
        self.alpha = alpha
        self.log = Logger(system=self)
        self.storage = storage or TalosLevelDBDHTStorage("./leveldb")
        self.c1bits = c1bits

        if priv_key is None:
            self.priv_key, node_id = generate_keys_with_crypto_puzzle(c1bits)
        else:
            self.priv_key = priv_key
            node_id = pub_to_node_id(self.priv_key.public_key())

        self.node = Node(node_id)

        def start_looping_call(num_seconds):
            self.refreshLoop = LoopingCall(self.refreshTable).start(num_seconds)
        self.delay = rebub_delay
        task.deferLater(reactor, rebub_delay, start_looping_call, rebub_delay)

        self.talos_vc = talos_vc or AsyncPolicyApiClient()
        self.protocol = TalosSKademliaProtocol(self.priv_key, self.node,
                                               self.storage, ksize, talos_vc=self.talos_vc)
        self.httpprotocol_client = None

    def saveState(self, fname):
        """
        Save the state of this node (the alpha/ksize/id/immediate neighbors)
        to a cache file with the given fname.
        """
        self.log.info("Save state to file %s" % fname)
        data = { 'ksize': self.ksize,
                 'alpha': self.alpha,
                 'priv_key': serialize_priv_key(self.priv_key),
                 'c1bits': self.c1bits,
                 'neighbors': self.bootstrappableNeighbors()}
        if len(data['neighbors']) == 0:
            self.log.warning("No known neighbors, so not writing to cache.")
            return
        with open(fname, 'w') as f:
            pickle.dump(data, f)

    @classmethod
    def loadState(self, fname, storage=None, talos_vc=None):
        """
        Load the state of this node (the alpha/ksize/id/immediate neighbors)
        from a cache file with the given fname.
        """
        with open(fname, 'r') as f:
            data = pickle.load(f)
        s = TalosSecureDHTServer(data['ksize'], data['alpha'], deserialize_priv_key(data['priv_key']),
                                 storage=None, talos_vc=None, c1bits=data['c1bits'])
        if len(data['neighbors']) > 0:
            s.bootstrap(data['neighbors'])
        return s