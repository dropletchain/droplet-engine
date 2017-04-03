import base64
import json
from StringIO import StringIO

from twisted.internet import reactor
from twisted.python import log
import itertools
import sys
from twisted.web.client import Agent, FileBodyProducer, readBody
from twisted.web.http_headers import Headers

from talosdht.dhtstorage import TalosLevelDBDHTStorage
from talosdht.server import TalosDHTServer
from talosdht.test.testutil import generate_token, generate_random_chunk
from talosstorage.chunkdata import CloudChunk

log.startLogging(sys.stdout)

start_port = 12000
num_servers = 100
servers = []
counter_iter = itertools.count()


class TwistedHTTPClient:
    def __init__(self):
        self.agent = Agent(reactor)

    def get_nonce(self, ip, port):
        d = self.agent.request(
            'GET',
            'http://%s:%d/get_chunk' % (ip, port),
            Headers({'User-Agent': ['TalosDHTNode']}),
            None)

        def handle_response(response):
            return readBody(response)

        return d.addCallback(handle_response)

    def get_chunk(self,ip, port, token):
        body = FileBodyProducer(StringIO(json.dumps(token.to_json())))
        d = self.agent.request(
            'POST',
            'http://%s:%d/get_chunk' % (ip, port),
            Headers({'User-Agent': ['TalosDHTNode']}),
            body)

        def handle_response(response):
            return readBody(response)

        return d.addCallback(handle_response)

for count in range(num_servers):
    storage = TalosLevelDBDHTStorage("./db/leveldb%d" % (count+1,))
    server = TalosDHTServer(ksize=4, storage=storage)
    server.listen(start_port + count)
    servers.append(server)


def have_chunk(result, (client, old_chunk, block_id)):
    if result is None:
        print "No value :("
        reactor.stop()
        return
    result = CloudChunk.decode(result)
    if isinstance(result, CloudChunk):
        print "Result %s" % result.get_base64_encoded()
    else:
        print result
    reactor.stop()


def have_nonce(nonce, (client, ip, port, chunk, block_id)):
    token = generate_token(block_id, nonce)
    print "with token %s \n" % token.to_json()
    return client.get_chunk(ip, int(port), token).addCallback(have_chunk, (client, chunk, block_id))


def setDone(address, (server, chunk, block_id)):
    print "Ask for key %s \n" % chunk.get_key_hex()
    client = TwistedHTTPClient()
    [ip, port] = address.split(':')
    return client.get_nonce(ip, int(port)).addCallback(have_nonce, (client, ip, port, chunk, block_id))


def findAddr(result, (server, chunk, block_id)):
    return server.get_addr_chunk(chunk.key).addCallback(setDone, (server, chunk, block_id))

def bootstrapDone(found, server):
    count = counter_iter.next()
    print "Server %d bootstrap done\n" % count
    if count == num_servers:
        chunk = generate_random_chunk(0, size=100000)
        servers[0].store_chunk(chunk).addCallback(findAddr, (servers[-1], chunk, 0))
    else:
        servers[count].bootstrap([('127.0.0.1', start_port + count - 1)]).addCallback(bootstrapDone, servers[count])


count = counter_iter.next()
servers[count].bootstrap([('127.0.0.1', start_port)]).addCallback(bootstrapDone, servers[count])

reactor.run()


