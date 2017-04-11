import json
import os
import random
from binascii import hexlify, unhexlify

from StringIO import StringIO
from threading import Semaphore

from cachetools import TTLCache
from kademlia.log import Logger
from kademlia.routing import RoutingTable, KBucket
from twisted.internet import defer, reactor

from kademlia.node import Node
from kademlia.utils import digest
from twisted.internet.task import LoopingCall
from twisted.web.client import Agent, FileBodyProducer, readBody, HTTPConnectionPool
from twisted.web.http_headers import Headers
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET

from talosdht.talosudprpc import TalosRPCProtocol, TalosWeakSignedRPCProtocol
from talosstorage.checks import check_query_token_valid, InvalidQueryToken, get_and_check_query_token, CloudChunk
from talosstorage.storage import InvalidChunkError
from talosstorage.timebench import TimeKeeper
from talosvc.talosclient.restapiclient import TalosVCRestClient, TalosVCRestClientError
from talosdht.util import *

MAX_UDP_SIZE = 8000

######################
# Fixed Routing Table #
######################


class TalosKBucket(KBucket):
    def isNewNode(self, node):
        return node.id not in self.nodes and node not in self.replacementNodes

    def split(self):
        midpoint = (self.range[0] + self.range[1]) / 2
        one = TalosKBucket(self.range[0], midpoint, self.ksize)
        two = TalosKBucket(midpoint + 1, self.range[1], self.ksize)
        for node in self.nodes.values():
            bucket = one if node.long_id <= midpoint else two
            bucket.nodes[node.id] = node
        return (one, two)


class TalosKademliaRoutingTable(RoutingTable):

    def flush(self):
        self.buckets = [TalosKBucket(0, 2 ** 160, self.ksize)]



######################
# Talos RPC Prototol #
######################


class TalosKademliaProtocol(TalosRPCProtocol):
    """
    New protocol for the talos storage, base protocol from bmuller's implementation
    """

    def __init__(self, sourceNode, storage, ksize, talos_vc=TalosVCRestClient()):
        TalosRPCProtocol.__init__(self)
        self.router = TalosKademliaRoutingTable(self, ksize, sourceNode)
        self.storage = storage
        self.sourceNode = sourceNode
        self.log = Logger(system=self)
        self.talos_vc = talos_vc
        self.http_client = None

    def getRefreshIDs(self):
        """
        Get ids to search for to keep old buckets up to date.
        """
        ids = []
        for bucket in self.router.getLonelyBuckets():
            ids.append(random.randint(*bucket.range))
        return ids

    def rpc_stun(self, sender):
        return sender

    def rpc_ping(self, sender, nodeid):
        source = Node(nodeid, sender[0], sender[1])
        self.welcomeIfNewNode(source)
        return self.sourceNode.id

    def rpc_store(self, sender, nodeid, key, value):
        source = Node(nodeid, sender[0], sender[1])
        time_keeper = TimeKeeper()
        time_keeper.start_clock()
        self.welcomeIfNewNode(source)
        time_keeper.stop_clock(ENTRY_TIME_WELCOME_NODE)

        self.log.debug("got a store request from %s, storing value" % str(sender))
        try:

            time_keeper.start_clock()
            chunk = CloudChunk.decode(value)
            time_keeper.stop_clock(ENTRY_TIME_DECODE_CHUNK)

            if not digest(chunk.key) == key:
                return {'error': 'key missmatch'}

            def handle_policy(policy):
                time_keeper.stop_clock(ENTRY_FETCH_POLICY)

                # Hack no chunk id given -> no key checks, key is in the encoded chunk
                id = time_keeper.start_clock_unique()
                self.storage.store_check_chunk(chunk, None, policy, time_keeper=time_keeper)
                time_keeper.stop_clock_unique(ENTRY_STORE_CHECK, id)

                self.log.debug("%s %s %s" % (BENCH_TAG, TYPE_STORE_CHUNK_LOCAL, time_keeper.get_summary()))
                return {'value': 'ok'}

            time_keeper.start_clock()
            return self.talos_vc.get_policy_with_txid(chunk.get_tag_hex()).addCallback(handle_policy)
        except InvalidChunkError as e:
            return {'error': e.value}
        except TalosVCRestClientError:
            return {'error': "No policy found"}

    def rpc_find_node(self, sender, nodeid, key):
        self.log.info("finding neighbors of %i in local table" % long(nodeid.encode('hex'), 16))
        source = Node(nodeid, sender[0], sender[1])
        self.welcomeIfNewNode(source)
        node = Node(key)
        return map(tuple, self.router.findNeighbors(node, exclude=source))

    def rpc_find_value(self, sender, nodeid, key, chunk_key):
        source = Node(nodeid, sender[0], sender[1])
        self.welcomeIfNewNode(source)
        if self.storage.has_value(chunk_key):
            try:
                myaddress = self.transport.getHost()
                return {'value': "%s:%d" % (myaddress.host, myaddress.port)}
            except InvalidQueryToken as e:
                self.log.info("Invalid query token received %s" % (e.value,))
                return {'error': e.value}
        else:
            return self.rpc_find_node(sender, nodeid, key)

    def callFindNode(self, nodeToAsk, nodeToFind):
        address = (nodeToAsk.ip, nodeToAsk.port)
        d = self.find_node(address, self.sourceNode.id, nodeToFind.id)
        return d.addCallback(self.handleCallResponse, nodeToAsk)

    def callFindValue(self, nodeToAsk, nodeToFind, chunk_key):
        address = (nodeToAsk.ip, nodeToAsk.port)
        d = self.find_value(address, self.sourceNode.id, nodeToFind.id, chunk_key)
        return d.addCallback(self.handleCallResponse, nodeToAsk)

    def callPing(self, nodeToAsk):
        address = (nodeToAsk.ip, nodeToAsk.port)
        d = self.ping(address, self.sourceNode.id)
        return d.addCallback(self.handleCallResponse, nodeToAsk)

    def callStore(self, nodeToAsk, key, value):
        address = (nodeToAsk.ip, nodeToAsk.port)
        time_keeper = TimeKeeper()
        id = time_keeper.start_clock_unique()
        if len(value) < MAX_UDP_SIZE:
            d = self.store(address, self.sourceNode.id, key, value)
        else:
            d = self.http_client.call_store_large_chunk(nodeToAsk, key, value)
        return d.addCallback(self.handleTimedCallResponse, nodeToAsk, time_keeper, id, ENTRY_STORE_ONE_NODE)

    def welcomeIfNewNode(self, node):
        """
        Given a new node, send it all the keys/values it should be storing,
        then add it to the routing table.

        @param node: A new node that just joined (or that we just found out
        about).

        Process:
        For each key in storage, get k closest nodes.  If newnode is closer
        than the furtherst in that list, and the node for this server
        is closer than the closest in that list, then store the key/value
        on the new node (per section 2.5 of the paper)
        """
        if self.router.isNewNode(node):
            ds = []
            """
               for key, value in self.storage.iteritems():
                   keynode = Node(digest(key))
                   neighbors = self.router.findNeighbors(keynode)
                   if len(neighbors) > 0:
                       newNodeClose = node.distanceTo(keynode) < neighbors[-1].distanceTo(keynode)
                       thisNodeClosest = self.sourceNode.distanceTo(keynode) < neighbors[0].distanceTo(keynode)
                   #if len(neighbors) == 0 or (newNodeClose and thisNodeClosest):
                       #ds.append(self.callStore(node, digest(key), value))
            """
            self.router.addContact(node)
            return defer.gatherResults(ds)

    def handleCallResponse(self, result, node):
        """
        If we get a response, add the node to the routing table.  If
        we get no response, make sure it's removed from the routing table.
        """
        if result[0]:
            self.log.info("got response from %s, adding to router" % node)
            self.welcomeIfNewNode(node)
        else:
            self.log.debug("no response from %s, removing from router" % node)
            self.router.removeContact(node)
        return result

    def handleTimedCallResponse(self, result, node, time_keeper, id, name):
        """
        If we get a response, add the node to the routing table.  If
        we get no response, make sure it's removed from the routing table.
        """
        time_keeper.stop_clock_unique(name, id)
        self.log.debug("%s %s %s " % (BENCH_TAG, TYPE_STORE_CHUNK_REMOTE, time_keeper.get_summary()))

        if result[0]:
            self.log.info("got response from %s, adding to router" % node)
            self.welcomeIfNewNode(node)
        else:
            self.log.debug("no response from %s, removing from router" % node)
            self.router.removeContact(node)
        return result


#################
# http protocol #
#################


class QueryChunk(Resource):
    allowedMethods = ('GET', 'POST')

    def __init__(self, storage, talos_vc=TalosVCRestClient(), max_nonce_cache=1000, nonce_ttl=10):
        Resource.__init__(self)
        self.storage = storage
        self.log = Logger(system=self)
        self.talos_vc = talos_vc
        self.nonce_cache = TTLCache(max_nonce_cache, nonce_ttl)
        self.refreshLoop = LoopingCall(self.nonce_cache.expire).start(3600)
        self.sem = Semaphore(1)

    def render_GET(self, request):
        nonce = os.urandom(16)
        self.nonce_cache[nonce] = True
        return nonce

    def _check_cache(self, nonce):
        self.sem.acquire(True)
        try:
            ok = self.nonce_cache[nonce]
            if ok:
                self.nonce_cache[nonce] = False
            return ok
        except KeyError:
            return False
        finally:
            self.sem.release()

    def render_POST(self, request):
        msg = json.loads(request.content.read())
        timekeeper = TimeKeeper()
        try:
            timekeeper.start_clock()
            token = get_and_check_query_token(msg)
            check_query_token_valid(token)
            timekeeper.stop_clock('check_token_valid')

            # Check nonce ok
            if not self._check_cache(token.nonce):
                raise InvalidQueryToken("Nonce not valid")

            def handle_policy(policy):
                timekeeper.stop_clock('time_fetch_policy')
                if policy is None:
                    request.setResponseCode(400)
                    request.write("No Policy Found")
                    request.finish()
                # check policy for correctness
                id = timekeeper.start_clock_unique()
                chunk = self.storage.get_check_chunk(token.chunk_key, token.pubkey, policy, time_keeper=timekeeper)
                timekeeper.stop_clock_unique('time_get_and_check-chunk', id)
                self.log.debug("[BENCH] QUERY CHUNK ->%s" % timekeeper.get_summary())

                request.write(chunk.encode())
                request.finish()
            timekeeper.start_clock()
            self.talos_vc.get_policy(token.owner, token.streamid).addCallback(handle_policy)
            return NOT_DONE_YET
        except InvalidQueryToken:
            request.setResponseCode(400)
            return "ERROR: token verification failure"
        except TalosVCRestClientError:
            request.setResponseCode(400)
            return "ERROR: No policy found"
        except:
            request.setResponseCode(400)
            return "ERROR: error occured"


# POST /storelargechunk/<hex node-id>/<port>/<hex key>
class StoreLargeChunk(Resource):
    allowedMethods = ('POST',)

    def __init__(self, storage, rpc_protocol, talos_vc=TalosVCRestClient()):
        Resource.__init__(self)
        self.storage = storage
        self.log = Logger(system=self)
        self.talos_vc = talos_vc
        self.rpc_protocol = rpc_protocol

    def getChild(self, path, request):
        return self

    def render_POST(self, request):
        if len(request.prepath) < 4:
            request.setResponseCode(400)
            return json.dumps({'error': "Illegal URL"})
        try:
            time_keeper = TimeKeeper()
            nodeid = unhexlify(request.prepath[1])
            source_ip = request.client.host
            source_port = int(request.prepath[2])
            kad_key = unhexlify(request.prepath[3])

            source = Node(nodeid, source_ip, source_port)

            time_keeper.start_clock()
            self.rpc_protocol.welcomeIfNewNode(source)
            time_keeper.stop_clock("time_welcome_node")

            encoded_chunk = request.content.read()

            time_keeper.start_clock()
            chunk = CloudChunk.decode(encoded_chunk)
            time_keeper.stop_clock("time_decode_chunk")

            if not digest(chunk.key) == kad_key:
                request.setResponseCode(400)
                return json.dumps({'error': "key missmatch"})

            def handle_policy(policy):
                time_keeper.stop_clock("time_fetch_policy")

                id = time_keeper.start_clock_unique()
                self.storage.store_check_chunk(chunk, None, policy)
                time_keeper.stop_clock_unique("time_store_check_chunk", id)

                self.log.debug("[BENCH] STORE LARGE NODE %s ->%s" % (str(source), time_keeper.get_summary()))
                request.write(json.dumps({'value': "ok"}))
                request.finish()

            time_keeper.start_clock()
            self.talos_vc.get_policy_with_txid(chunk.get_tag_hex()).addCallback(handle_policy)
            return NOT_DONE_YET
        except InvalidChunkError as e:
            request.setResponseCode(400)
            return json.dumps({'error': e.value})
        except TalosVCRestClientError:
            request.setResponseCode(400)
            return "ERROR: No policy found"
        except:
            request.setResponseCode(400)
            return json.dumps({'error': "Error occured"})


class TalosHTTPClient:
    def __init__(self, rpc_protocol, my_tcp_port):
        self.pool = HTTPConnectionPool(reactor)
        self.agent = Agent(reactor, pool=self.pool)
        self.rpc_protocol = rpc_protocol
        self.my_tcp_port = my_tcp_port

    def call_store_large_chunk(self, nodeToAsk, key, value):
        res = "storelargechunk/%s/%d/%s" % (hexlify(self.rpc_protocol.sourceNode.id),
                                            self.my_tcp_port,
                                            hexlify(key))
        body = FileBodyProducer(StringIO(value))
        d = self.agent.request(
            'POST',
            'http://%s:%d/%s' % (nodeToAsk.ip, nodeToAsk.port, res),
            Headers({'User-Agent': ['TalosDHTNode']}),
            body)

        def handle_result_value(body):
            return True, json.loads(body)

        def handle_response(response):
            d = readBody(response)
            return d.addCallback(handle_result_value)

        def handle_error(error):
            return False, None

        return d.addCallbacks(handle_response, errback=handle_error)


class TalosSKademliaProtocol(TalosWeakSignedRPCProtocol):
    """
    New protocol for the talos storage, base protocol from bmuller's implementation
    """

    def __init__(self, ecdsa_privkey, sourceNode, storage, ksize, talos_vc=TalosVCRestClient()):
        TalosWeakSignedRPCProtocol.__init__(self, ecdsa_privkey, sourceNode.id)
        self.router = TalosKademliaRoutingTable(self, ksize, sourceNode)
        self.storage = storage
        self.sourceNode = sourceNode
        self.log = Logger(system=self)
        self.talos_vc = talos_vc
        self.http_client = None

    def getRefreshIDs(self):
        """
        Get ids to search for to keep old buckets up to date.
        """
        ids = []
        for bucket in self.router.getLonelyBuckets():
            ids.append(random.randint(*bucket.range))
        return ids

    def rpc_stun(self, sender):
        return sender

    def rpc_ping(self, sender, nodeid):
        source = Node(nodeid, sender[0], sender[1])
        self.welcomeIfNewNode(source)
        return self.sourceNode.id

    def rpc_store(self, sender, nodeid, key, value):
        source = Node(nodeid, sender[0], sender[1])
        time_keeper = TimeKeeper()
        time_keeper.start_clock()
        self.welcomeIfNewNode(source)
        time_keeper.stop_clock(ENTRY_TIME_WELCOME_NODE)

        self.log.debug("got a store request from %s, storing value" % str(sender))
        try:

            time_keeper.start_clock()
            chunk = CloudChunk.decode(value)
            time_keeper.stop_clock(ENTRY_TIME_DECODE_CHUNK)

            if not digest(chunk.key) == key:
                return {'error': 'key missmatch'}

            def handle_policy(policy):
                time_keeper.stop_clock(ENTRY_FETCH_POLICY)

                # Hack no chunk id given -> no key checks, key is in the encoded chunk
                id = time_keeper.start_clock_unique()
                self.storage.store_check_chunk(chunk, None, policy, time_keeper=time_keeper)
                time_keeper.stop_clock_unique(ENTRY_STORE_CHECK, id)

                self.log.debug("%s %s %s" % (BENCH_TAG, TYPE_STORE_CHUNK_LOCAL, time_keeper.get_summary()))
                return {'value': 'ok'}

            time_keeper.start_clock()
            return self.talos_vc.get_policy_with_txid(chunk.get_tag_hex()).addCallback(handle_policy)
        except InvalidChunkError as e:
            return {'error': e.value}
        except TalosVCRestClientError:
            return {'error': "No policy found"}

    def rpc_find_node(self, sender, nodeid, key):
        self.log.info("finding neighbors of %i in local table" % long(nodeid.encode('hex'), 16))
        source = Node(nodeid, sender[0], sender[1])
        self.welcomeIfNewNode(source)
        node = Node(key)
        return map(tuple, self.router.findNeighbors(node, exclude=source))

    def rpc_find_value(self, sender, nodeid, key, chunk_key):
        source = Node(nodeid, sender[0], sender[1])
        self.welcomeIfNewNode(source)
        if self.storage.has_value(chunk_key):
            try:
                myaddress = self.transport.getHost()
                return {'value': "%s:%d" % (myaddress.host, myaddress.port)}
            except InvalidQueryToken as e:
                self.log.info("Invalid query token received %s" % (e.value,))
                return {'error': e.value}
        else:
            return self.rpc_find_node(sender, nodeid, key)

    def callFindNode(self, nodeToAsk, nodeToFind):
        address = (nodeToAsk.ip, nodeToAsk.port)
        d = self.find_node(address, self.sourceNode.id, nodeToFind.id)
        return d.addCallback(self.handleCallResponse, nodeToAsk)

    def callFindValue(self, nodeToAsk, nodeToFind, chunk_key):
        address = (nodeToAsk.ip, nodeToAsk.port)
        d = self.find_value(address, self.sourceNode.id, nodeToFind.id, chunk_key)
        return d.addCallback(self.handleCallResponse, nodeToAsk)

    def callPing(self, nodeToAsk):
        address = (nodeToAsk.ip, nodeToAsk.port)
        d = self.ping(address, self.sourceNode.id)
        return d.addCallback(self.handleCallResponse, nodeToAsk)

    def callStore(self, nodeToAsk, key, value):
        address = (nodeToAsk.ip, nodeToAsk.port)
        time_keeper = TimeKeeper()
        id = time_keeper.start_clock_unique()
        if len(value) < MAX_UDP_SIZE:
            d = self.store(address, self.sourceNode.id, key, value)
        else:
            d = self.http_client.call_store_large_chunk(nodeToAsk, key, value)
        return d.addCallback(self.handleTimedCallResponse, nodeToAsk, time_keeper, id, ENTRY_STORE_ONE_NODE)

    def welcomeIfNewNode(self, node):
        """
        Given a new node, send it all the keys/values it should be storing,
        then add it to the routing table.

        @param node: A new node that just joined (or that we just found out
        about).

        Process:
        For each key in storage, get k closest nodes.  If newnode is closer
        than the furtherst in that list, and the node for this server
        is closer than the closest in that list, then store the key/value
        on the new node (per section 2.5 of the paper)
        """
        if self.router.isNewNode(node):
            ds = []
            """
               for key, value in self.storage.iteritems():
                   keynode = Node(digest(key))
                   neighbors = self.router.findNeighbors(keynode)
                   if len(neighbors) > 0:
                       newNodeClose = node.distanceTo(keynode) < neighbors[-1].distanceTo(keynode)
                       thisNodeClosest = self.sourceNode.distanceTo(keynode) < neighbors[0].distanceTo(keynode)
                   #if len(neighbors) == 0 or (newNodeClose and thisNodeClosest):
                       #ds.append(self.callStore(node, digest(key), value))
            """
            self.router.addContact(node)
            return defer.gatherResults(ds)

    def handleCallResponse(self, result, node):
        """
        If we get a response, add the node to the routing table.  If
        we get no response, make sure it's removed from the routing table.
        """
        if result[0]:
            self.log.info("got response from %s, adding to router" % node)
            self.welcomeIfNewNode(node)
        else:
            self.log.debug("no response from %s, removing from router" % node)
            self.router.removeContact(node)
        return result

    def handleTimedCallResponse(self, result, node, time_keeper, id, name):
        """
        If we get a response, add the node to the routing table.  If
        we get no response, make sure it's removed from the routing table.
        """
        time_keeper.stop_clock_unique(name, id)
        self.log.debug("%s %s %s " % (BENCH_TAG, TYPE_STORE_CHUNK_REMOTE, time_keeper.get_summary()))

        if result[0]:
            self.log.info("got response from %s, adding to router" % node)
            self.welcomeIfNewNode(node)
        else:
            self.log.debug("no response from %s, removing from router" % node)
            self.router.removeContact(node)
        return result
