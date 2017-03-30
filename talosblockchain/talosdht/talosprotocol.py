import random

from kademlia.log import Logger
from kademlia.protocol import KademliaProtocol
from kademlia.routing import RoutingTable
from twisted.internet import defer

from rpcudp.protocol import RPCProtocol

from kademlia.node import Node
from kademlia.utils import digest
from talosstorage.checks import check_query_token_valid, InvalidQueryToken, get_and_check_query_token, CloudChunk
from talosstorage.storage import InvalidChunkError
from talosvc.talosclient.restapiclient import TalosVCRestClient


class TalosKademliaProtocol(RPCProtocol):
    """
    New protocol for the talos storage, base protocol from bmuller's implementation
    """
    def __init__(self, sourceNode, storage, ksize, talos_vc=TalosVCRestClient(), max_time_check=10):
        RPCProtocol.__init__(self)
        self.router = RoutingTable(self, ksize, sourceNode)
        self.storage = storage
        self.sourceNode = sourceNode
        self.log = Logger(system=self)
        self.max_time_check = max_time_check
        self.talos_vc = talos_vc

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
        self.welcomeIfNewNode(source)
        self.log.debug("got a store request from %s, storing value" % str(sender))
        try:
            chunk = CloudChunk.decode(value)
            if not digest(chunk.key) == key:
                return {'error': 'key missmatch'}
            policy = self.talos_vc.get_policy_with_txid(chunk.get_tag_hex())
            # Hack no chunk id given -> no key checks, key is in the encoded chunk
            self.storage.store_check_chunk(chunk, None, policy)
        except InvalidChunkError as e:
            return {'error': e.value}
        return {'value': 'ok'}

    def rpc_find_node(self, sender, nodeid, key):
        self.log.info("finding neighbors of %i in local table" % long(nodeid.encode('hex'), 16))
        source = Node(nodeid, sender[0], sender[1])
        self.welcomeIfNewNode(source)
        node = Node(key)
        return map(tuple, self.router.findNeighbors(node, exclude=source))

    def rpc_find_value(self, sender, nodeid, key, token):
        source = Node(nodeid, sender[0], sender[1])
        self.welcomeIfNewNode(source)
        token = get_and_check_query_token(token)
        if self.storage.has_value(token.chunk_key):
            try:
                self.log.info("Check access correct (value found) %s" % nodeid.encode('hex'))
                check_query_token_valid(token, self.max_time_check)
                policy = self.talos_vc.get_policy(token.owner, token.streamid)
                # check policy for correctness
                chunk = self.storage.get_check_chunk(token.chunk_key, token.pubkey, policy)
                if not digest(chunk.key) == key:
                    return {'error': 'key missmatch'}
                return {'value': chunk.encode()}
            except InvalidQueryToken as e:
                self.log.info("Invalid query token received %s" % (e.value,))
                return {'error': e.value}
        else:
            return self.rpc_find_node(sender, nodeid, key)

    def callFindNode(self, nodeToAsk, nodeToFind):
        address = (nodeToAsk.ip, nodeToAsk.port)
        d = self.find_node(address, self.sourceNode.id, nodeToFind.id)
        return d.addCallback(self.handleCallResponse, nodeToAsk)

    def callFindValue(self, nodeToAsk, nodeToFind, token):
        address = (nodeToAsk.ip, nodeToAsk.port)
        d = self.find_value(address, self.sourceNode.id, nodeToFind.id, token)
        return d.addCallback(self.handleCallResponse, nodeToAsk)

    def callPing(self, nodeToAsk):
        address = (nodeToAsk.ip, nodeToAsk.port)
        d = self.ping(address, self.sourceNode.id)
        return d.addCallback(self.handleCallResponse, nodeToAsk)

    def callStore(self, nodeToAsk, key, value):
        address = (nodeToAsk.ip, nodeToAsk.port)
        d = self.store(address, self.sourceNode.id, key, value)
        return d.addCallback(self.handleCallResponse, nodeToAsk)

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
            for key, value in self.storage.iteritems():
                keynode = Node(digest(key))
                neighbors = self.router.findNeighbors(keynode)
                if len(neighbors) > 0:
                    newNodeClose = node.distanceTo(keynode) < neighbors[-1].distanceTo(keynode)
                    thisNodeClosest = self.sourceNode.distanceTo(keynode) < neighbors[0].distanceTo(keynode)
                if len(neighbors) == 0 or (newNodeClose and thisNodeClosest):
                    ds.append(self.callStore(node, key, value))
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