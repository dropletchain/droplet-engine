#© 2017-2020, ETH Zurich, D-INFK, lubu@inf.ethz.ch

from rpcudp.protocol import RPCProtocol
from twisted.internet import reactor

from test_storage_api import generate_random_chunk, generate_token


class RPCClient(RPCProtocol):

    def handleResult(self, result):
    	# result will be a tuple - first arg is a boolean indicating whether a response
        # was received, and the second argument is the response if one was received.
        if result[0]:
            print "Success! %s" % result[1]
        else:
            print "Response not received."

token = generate_token()
chunk = generate_random_chunk(0)
client = RPCClient()
reactor.listenUDP(5678, client)
client.sayhi(('127.0.0.1', 1234), chunk.encode(), token.to_json()).addCallback(client.handleResult)
reactor.run()