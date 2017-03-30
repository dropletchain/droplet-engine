import base64

from twisted.internet import reactor
from twisted.python import log
import itertools

import sys

from talosdht.dhtstorage import TalosLevelDBDHTStorage
from talosdht.server import TalosDHTServer
from talosdht.test.testutil import generate_token, generate_random_chunk
from talosstorage.chunkdata import CloudChunk

log.startLogging(sys.stdout)

start_port = 12000
num_servers = 100
servers = []
counter_iter = itertools.count()


for count in range(num_servers):
    storage = TalosLevelDBDHTStorage("./db/leveldb%d" % (count+1,))
    server = TalosDHTServer(ksize=4, storage=storage)
    server.listen(start_port + count)
    servers.append(server)


def done(result):
    if result is None:
        print "No value :("
        reactor.stop()
        return
    if isinstance(result, CloudChunk):
        print "Result %s" % result.get_base64_encoded()
    else:
        print result
    reactor.stop()


def setDone(result, (server, chunk, block_id)):
    print "Ask for key %s \n" % chunk.get_key_hex()
    token = generate_token(block_id)
    print "with token %s \n" % token.to_json()
    server.get_chunk(token).addCallback(done)


def bootstrapDone(found, server):
    count = counter_iter.next()
    print "Server %d bootstrap done\n" % count
    if count == num_servers:
        chunk = generate_random_chunk(0, size=10000)
        servers[0].store_chunk(chunk).addCallback(setDone, (servers[-1], chunk, 0))
    else:
        servers[count].bootstrap([('127.0.0.1', start_port + count - 1)]).addCallback(bootstrapDone, servers[count])


count = counter_iter.next()
servers[count].bootstrap([('127.0.0.1', start_port)]).addCallback(bootstrapDone, servers[count])

reactor.run()


