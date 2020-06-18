#© 2017-2020, ETH Zurich, D-INFK, lubu@inf.ethz.ch

from rpcudp.protocol import RPCProtocol
from twisted.internet import reactor

from talosstorage.checks import QueryToken
from talosstorage.chunkdata import CloudChunk


class RPCServer(RPCProtocol):
    # Any methods starting with "rpc_" are available to clients.
    def rpc_sayhi(self, sender, chunk, token):
        token = QueryToken.from_json(token)
        # This could return a Deferred as well. sender is (ip,port)
        chunk_orig = CloudChunk.decode(chunk)
        return "Tag is  %s you live at %s:%i and token is %s" % (chunk_orig.get_tag_hex(), sender[0], sender[1], token.owner)

# start a server on UDP port 1234
reactor.listenUDP(1234, RPCServer())
reactor.run()