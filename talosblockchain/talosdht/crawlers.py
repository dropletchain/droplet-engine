from collections import Counter

from kademlia.crawling import SpiderCrawl, RPCFindResponse
from kademlia.node import NodeHeap, Node
from kademlia.utils import deferredDict

from talosstorage.chunkdata import CloudChunk
from talosstorage.timebench import TimeKeeper


class TalosSpiderCrawl(SpiderCrawl):
    """
    Crawl the network and look for given 160-bit keys.
    """
    def __init__(self, protocol, node, chunk_key, peers, ksize, alpha):
        """
        Create a new C{SpiderCrawl}er.

        Args:
            protocol: A :class:`~kademlia.protocol.KademliaProtocol` instance.
            node: A :class:`~kademlia.node.Node` representing the key we're looking for
            peers: A list of :class:`~kademlia.node.Node` instances that provide the entry point for the network
            ksize: The value for k based on the paper
            alpha: The value for alpha based on the paper
        """
        SpiderCrawl.__init__(self, protocol, node, peers, ksize, alpha)
        self.chunk_key = chunk_key

    def _find_value(self, rpcmethod):
        """
        Get either a value or list of nodes.

        Args:
            rpcmethod: The protocol's callfindValue.

        The process:
          1. calls find_* to current ALPHA nearest not already queried nodes,
             adding results to current nearest list of k nodes.
          2. current nearest list needs to keep track of who has been queried already
             sort by nearest, keep KSIZE
          3. if list is same as last time, next call should be to everyone not
             yet queried
          4. repeat, unless nearest list has all been queried, then ur done
        """
        self.log.info("crawling with nearest: %s" % str(tuple(self.nearest)))
        count = self.alpha
        if self.nearest.getIDs() == self.lastIDsCrawled:
            self.log.info("last iteration same as current - checking all in list now")
            count = len(self.nearest)
        self.lastIDsCrawled = self.nearest.getIDs()

        ds = {}
        for peer in self.nearest.getUncontacted()[:count]:
            ds[peer.id] = rpcmethod(peer, self.node, self.chunk_key)
            self.nearest.markContacted(peer)
        return deferredDict(ds).addCallback(self._nodesFound)


class TalosChunkSpiderCrawl(TalosSpiderCrawl):
    def __init__(self, protocol, http_client, node, chunk_key, peers, ksize, alpha, time_keeper=TimeKeeper()):
        TalosSpiderCrawl.__init__(self, protocol, node, chunk_key, peers, ksize, alpha)
        # keep track of the single nearest node without value - per
        # section 2.3 so we can set the key there if found
        self.nearestWithoutValue = NodeHeap(self.node, 1)
        self.http_client = http_client
        self.time_keeper = time_keeper
        self.is_first_round = True

    def find(self):
        """
        Find either the closest nodes or the value requested.
        """
        if self.is_first_round:
            self.time_keeper.start_clock()
            self.is_first_round = False
        return self._find_value(self.protocol.callFindValue)

    def _nodesFound(self, responses):
        """
        Handle the result of an iteration in _find.
        """
        toremove = []
        foundValues = []
        for peerid, response in responses.items():
            response = TalosRPCFindValueResponse(response)
            if not response.happened():
                toremove.append(peerid)
            elif response.hasValue():
                foundValues.append(response.getValue())
            elif response.hasError():
                return response.getError()
            else:
                peer = self.nearest.getNodeById(peerid)
                self.nearestWithoutValue.push(peer)
                self.nearest.push(response.getNodeList())
        self.nearest.remove(toremove)

        if len(foundValues) > 0:
            return self._handleFoundValues(foundValues)
        if self.nearest.allBeenContacted():
            # not found!
            return None
        return self.find()

    def _handleFoundValues(self, values):
        """
        We got some values!  Exciting.  But let's make sure
        they're all the same or freak out a little bit.  Also,
        make sure we tell the nearest node that *didn't* have
        the value to store it.
        """
        self.time_keeper.stop_clock("time_find_value")
        self.log.debug("[BENCH] FIND VALUE CRAWL -> %s" % self.time_keeper.get_summary())

        valueCounts = Counter(values)
        if len(valueCounts) != 1:
            args = (self.node.long_id, str(values))
            self.log.warning("Got multiple values for key %i: %s" % args)
        value = valueCounts.most_common(1)[0][0]

        peerToSaveTo = self.nearestWithoutValue.popleft()
        if peerToSaveTo is not None:
            self.protocol.callStore(peerToSaveTo, self.node.id, value)
            return value
        return value


class TimedNodeSpiderCrawl(SpiderCrawl):

    def __init__(self, protocol, node, peers, ksize, alpha, time_keeper=TimeKeeper()):
        SpiderCrawl.__init__(self, protocol, node, peers, ksize, alpha)
        self.time_keeper = time_keeper
        self.is_first = True


    def find(self):
        """
        Find the closest nodes.
        """
        if self.is_first:
            self.time_keeper.start_clock()
            self.is_first = False
        return self._find(self.protocol.callFindNode)

    def _nodesFound(self, responses):
        """
        Handle the result of an iteration in _find.
        """
        toremove = []
        for peerid, response in responses.items():
            response = RPCFindResponse(response)
            if not response.happened():
                toremove.append(peerid)
            else:
                self.nearest.push(response.getNodeList())
        self.nearest.remove(toremove)

        if self.nearest.allBeenContacted():
            self.time_keeper.stop_clock("time_crawl_nearest")
            self.is_first = True
            return list(self.nearest)
        return self.find()


class TalosRPCFindValueResponse(object):
    def __init__(self, response):
        """
        A wrapper for the result of a RPC find.

        Args:
            response: This will be a tuple of (<response received>, <value>)
                      where <value> will be a list of tuples if not found or
                      a dictionary of {'value': v} where v is the value desired
        """
        self.response = response

    def happened(self):
        """
        Did the other host actually respond?
        """
        return self.response[0]

    def hasValue(self):
        return isinstance(self.response[1], dict) and 'value' in self.response[1]

    def hasError(self):
        return isinstance(self.response[1], dict) and 'error' in self.response[1]

    def getValue(self):
        return self.response[1]['value']

    def getError(self):
        return self.response[1]['error']

    def getNodeList(self):
        """
        Get the node list in the response.  If there's no value, this should
        be set.
        """
        nodelist = self.response[1] or []
        return [Node(*nodeple) for nodeple in nodelist]