import random
import unittest

from kademlia.node import Node
from kademlia.utils import digest

from talosdht.protocolsecurity import generate_secret_key
from talosdht.talosprotocol import TalosSKademliaProtocol
from talosvc.talosclient.restapiclient import TalosVCRestClient



class DummyProt(TalosSKademliaProtocol):
    def callPing(self, nodeToAsk):
        print "Ping %s" % nodeToAsk


class TestBuckets(unittest.TestCase):
    def test_bucket_basic(self):
        ecd_key = generate_secret_key()
        sourceNode = Node(digest(random.getrandbits(255)), ip="127.0.0.1", port=12345)
        dummy_protocol = DummyProt(ecd_key, sourceNode, None, 4, talos_vc=None)

        nodes = []
        for i in range(1000):
            nodes.append(Node(digest(random.getrandbits(255)), ip="127.0.0.1", port=i+10000))
        for i in range(1000):
            dummy_protocol.router.addContact(nodes[i])

        for i in range(1000):
            self.assertFalse(dummy_protocol.router.isNewNode(nodes[i]))


