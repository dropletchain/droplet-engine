import umsgpack
import os

from hashlib import sha1
from base64 import b64encode

from kademlia.log import Logger

from protocolsecurity import *
from twisted.internet import reactor, protocol
from twisted.internet import defer
from twisted.python import log

from rpcudp.exceptions import MalformedMessage

from talosstorage.timebench import TimeKeeper

MAX_UDP_SIZE_PCK = 8192


class TalosRPCProtocol(protocol.DatagramProtocol):
    def __init__(self, waitTimeout=10, max_packet_size=MAX_UDP_SIZE_PCK, noisy=False):
        self.max_packet_size = max_packet_size
        self.noisy = noisy
        self._waitTimeout = waitTimeout
        self._outstanding = {}
        self.log = Logger(system=self)

    def datagramReceived(self, datagram, address):
        time_keeper = TimeKeeper()

        if self.noisy:
            log.msg("received datagram from %s" % repr(address))
        if len(datagram) < 22:
            log.msg("received datagram too small from %s, ignoring" % repr(address))
            return

        msgID = datagram[1:21]
        time_keeper.start_clock()
        data = umsgpack.unpackb(datagram[21:])
        time_keeper.stop_clock("time_unpack_msg")

        #self.log.debug("[BENCH] LOW RPC RECEIVE -> %s " % (time_keeper.get_summary(),))

        if datagram[:1] == b'\x00':
            self._acceptRequest(msgID, data, address)
        elif datagram[:1] == b'\x01':
            self._acceptResponse(msgID, data, address)
        else:
            # otherwise, don't know the format, don't do anything
            log.msg("Received unknown message from %s, ignoring" % repr(address))

    def _acceptResponse(self, msgID, data, address):
        msgargs = (b64encode(msgID), address)
        if msgID not in self._outstanding:
            log.err("received unknown message %s from %s; ignoring" % msgargs)
            return
        if self.noisy:
            log.msg("received response for message id %s from %s" % msgargs)
        d, timeout = self._outstanding[msgID]
        timeout.cancel()
        d.callback((True, data))
        del self._outstanding[msgID]

    def _acceptRequest(self, msgID, data, address):
        if not isinstance(data, list) or len(data) != 3:
            raise MalformedMessage("Could not read packet: %s" % data)
        funcname, node_id, args = data
        f = getattr(self, "rpc_%s" % funcname, None)
        if f is None or not callable(f):
            msgargs = (self.__class__.__name__, funcname)
            log.err("%s has no callable method rpc_%s; ignoring request" % msgargs)
            return
        d = defer.maybeDeferred(f, address, node_id, *args)
        d.addCallback(self._sendResponse, msgID, address)

    def _sendResponse(self, response, msgID, address):
        if self.noisy:
            log.msg("sending response for msg id %s to %s" % (b64encode(msgID), address))
        txdata = b'\x01' + msgID + umsgpack.packb(response)
        self.transport.write(txdata, address)

    def _timeout(self, msgID):
        args = (b64encode(msgID), self._waitTimeout)
        log.err("Did not received reply for msg id %s within %i seconds" % args)
        self._outstanding[msgID][0].callback((False, None))
        del self._outstanding[msgID]

    def __getattr__(self, name):
        if name.startswith("_") or name.startswith("rpc_"):
            return object.__getattr__(self, name)

        try:
            return object.__getattr__(self, name)
        except AttributeError:
            pass

        def func(address, node_id, *args):
            time_keeper = TimeKeeper()
            msgID = sha1(os.urandom(32)).digest()
            assert len(node_id) == 20
            time_keeper.start_clock()
            data = umsgpack.packb([str(name), node_id, args])
            time_keeper.stop_clock("time_data_pack")

            if len(data) > self.max_packet_size:
                msg = "Total length of function name and arguments cannot exceed 8K"
                raise MalformedMessage(msg)
            txdata = b'\x00' + msgID + data
            if self.noisy:
                log.msg("calling remote function %s on %s (msgid %s)" % (name, address, b64encode(msgID)))
            time_keeper.start_clock()
            self.transport.write(txdata, address)
            time_keeper.stop_clock("time_write_socket")

            #self.log.debug("[BENCH] LOW RPC SEND TIMES %s -> %s " % (str(name), time_keeper.get_summary()))

            d = defer.Deferred()
            timeout = reactor.callLater(self._waitTimeout, self._timeout, msgID)
            self._outstanding[msgID] = (d, timeout)
            return d
        return func

    def get_address(self):
        host = self.transport.getHost()
        return host.host, host.port


class TalosWeakSignedRPCProtocol(TalosRPCProtocol):
    def __init__(self, ecdsa_privkey, my_node_id, waitTimeout=10, max_packet_size=MAX_UDP_SIZE_PCK, noisy=False):
        TalosRPCProtocol.__init__(self, waitTimeout=waitTimeout, max_packet_size=max_packet_size, noisy=noisy)
        self.private_key = ecdsa_privkey
        self.public_key = ecdsa_privkey.public_key()
        self.ser_pub = serialize_pub_key(self.public_key)
        self.my_node_id = my_node_id
        self.cbits = 10

    def _acceptResponse(self, msgID, data, address):
        if not isinstance(data, list) or len(data) != 4:
            raise MalformedMessage("Could not read packet: %s" % data)
        msgargs = (b64encode(msgID), address)
        if msgID not in self._outstanding:
            log.err("received unknown message %s from %s; ignoring" % msgargs)
            return
        if self.noisy:
            log.msg("received response for message id %s from %s" % msgargs)
        d, timeout = self._outstanding[msgID]
        timeout.cancel()
        del self._outstanding[msgID]
        node_id, signature, ser_pub, response = data
        if not self._check_resp_ok(address, node_id, msgID, signature, ser_pub):
            return
        d.callback((True, response))

    def _check_resp_ok(self, address, node_id, msgID, signature, ser_pub):
        ip, port = address
        pub_key = deserialize_pub_key(ser_pub)
        if not check_nonce_msg(ip, port, msgID, signature, pub_key):
            log.err("Invalid signature on message")
            return False
        if not check_pubkey(node_id, ser_pub):
            log.err("Pub key does not match node id")
            return False
        if not check_cbits(pub_to_id(node_id), self.cbits):
            log.err("Puzzle not solved")
            return False
        return True

    def _check_req_ok(self, address, node_id, timestamp, signature, ser_pub):
        ip, port = address
        if not check_time(timestamp):
            log.err("Received message with old timestamp")
            return False
        pub_key = deserialize_pub_key(ser_pub)
        if not check_msg(ip, port, timestamp, signature, pub_key):
            log.err("Invalid signature on message")
            return False
        if not check_pubkey(node_id, ser_pub):
            log.err("Pub key does not match node id")
            return False
        if not check_cbits(pub_to_id(node_id), self.cbits):
            log.err("Puzzle not solved")
            return False
        return True

    def _acceptRequest(self, msgID, data, address):
        if not isinstance(data, list) or len(data) != 6:
            raise MalformedMessage("Could not read packet: %s" % data)
        funcname, node_id, timestamp, signature, ser_pub, args = data
        if not self._check_req_ok(address, node_id, timestamp, signature, ser_pub):
            return
        f = getattr(self, "rpc_%s" % funcname, None)
        if f is None or not callable(f):
            msgargs = (self.__class__.__name__, funcname)
            log.err("%s has no callable method rpc_%s; ignoring request" % msgargs)
            return
        d = defer.maybeDeferred(f, address, node_id, *args)
        d.addCallback(self._sendResponse, msgID, address)

    def _sendResponse(self, response, msgID, address):
        if self.noisy:
            log.msg("sending response for msg id %s to %s" % (b64encode(msgID), address))

        (my_ip, my_port) = self.get_address()
        signature = sign_nonce_msg(my_ip, my_port, msgID, self.private_key)
        ser_pub = serialize_pub_key(self.public_key)

        txdata = b'\x01' + msgID + umsgpack.packb([self.my_node_id, signature, ser_pub, response])
        self.transport.write(txdata, address)

    def __getattr__(self, name):
        if name.startswith("_") or name.startswith("rpc_"):
            return object.__getattr__(self, name)

        try:
            return object.__getattr__(self, name)
        except AttributeError:
            pass

        def func(address, node_id, *args):
            msgID = sha1(os.urandom(32)).digest()
            assert len(node_id) == 20
            (my_ip, my_port) = self.get_address()

            signature, timestamp = sign_msg(my_ip, my_port, self.private_key)
            ser_pub = serialize_pub_key(self.public_key)

            data = umsgpack.packb([str(name), node_id, timestamp, signature, ser_pub, args])
            if len(data) > self.max_packet_size:
                msg = "Total length of function name and arguments cannot exceed 8K"
                raise MalformedMessage(msg)
            txdata = b'\x00' + msgID + data
            if self.noisy:
                log.msg("calling remote function %s on %s (msgid %s)" % (name, address, b64encode(msgID)))
            self.transport.write(txdata, address)
            d = defer.Deferred()
            timeout = reactor.callLater(self._waitTimeout, self._timeout, msgID)
            self._outstanding[msgID] = (d, timeout)
            return d
        return func

