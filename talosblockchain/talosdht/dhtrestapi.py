#© 2017-2020, ETH Zurich, D-INFK, lubu@inf.ethz.ch

import binascii
import json

from kademlia.log import Logger
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET

from talosdht.util import *
from talosstorage.chunkdata import CloudChunk
from talosstorage.storage import InvalidChunkError
from talosstorage.timebench import TimeKeeper
from talosvc.talosclient.restapiclient import TalosVCRestClientError


class AddChunk(Resource):
    allowedMethods = ('POST',)

    def __init__(self, dhtstorage):
        Resource.__init__(self)
        self.dhtstorage = dhtstorage
        self.log = Logger(system=self)

    def render_POST(self, request):
        time_keeper = TimeKeeper()
        time_id = time_keeper.start_clock_unique()

        def respond(result):
            time_keeper.stop_clock_unique(ENTRY_TOTAL_ADD_CHUNK, time_id)
            self.log.debug("%s %s %s" % (BENCH_TAG, TYPE_ADD_CHUNK, time_keeper.get_summary()))
            if not result is None:
                request.setResponseCode(200)
                request.write("OK")
            else:
                request.setResponseCode(400)
                request.write("ERROR")
            request.finish()

        encoded_chunk = request.content.read()
        try:

            chunk = CloudChunk.decode(encoded_chunk)
            self.dhtstorage.store_chunk(chunk, time_keeper=time_keeper).addCallback(respond)
            return NOT_DONE_YET
        except InvalidChunkError:
            request.setResponseCode(400)
            return "ERROR: Invalid Chunk"
        except TalosVCRestClientError:
            request.setResponseCode(400)
            return "ERROR: No Policy found"
        except:
            request.setResponseCode(400)
            return "ERROR"


"""
<resource>/<hex chunk key>
"""


class GetChunkLoaction(Resource):
    allowedMethods = ('GET',)

    def __init__(self, dhtstorage):
        Resource.__init__(self)
        self.dhtstorage = dhtstorage
        self.log = Logger(system=self)

    def getChild(self, path, request):
        return self

    def render_GET(self, request):
        time_keeper = TimeKeeper()
        time_id = time_keeper.start_clock_unique()

        def respond(result):
            time_keeper.stop_clock_unique(ENTRY_TOTAL_QUERY_CHUNK, time_id)
            self.log.debug("%s %s %s" % (BENCH_TAG, TYPE_QUERY_CHUNK_ADDR, time_keeper.get_summary()))

            if result is None:
                request.setResponseCode(400)
                request.write("No Result found")
            else:
                request.setResponseCode(200)
                request.write(result)
            request.finish()

        if len(request.prepath) < 2:
            request.setResponseCode(400)
            return json.dumps({'error': "Illegal URL"})
        try:
            chunk_key = binascii.unhexlify(request.prepath[1])
            self.dhtstorage.get_addr_chunk(chunk_key, time_keeper=time_keeper).addCallback(respond)
            return NOT_DONE_YET
        except TalosVCRestClientError:
            request.setResponseCode(400)
            return "ERROR: No Policy found"
        except:
            request.setResponseCode(400)
            return "ERROR"


"""
class GetChunkLoaction(Resource):
    allowedMethods = ('GET',)

    def __init__(self, dhtstorage):
        Resource.__init__(self)
        self.dhtstorage = dhtstorage

    def render_GET(self, request):
        def respond(result):
            if result is None:
                request.setResponseCode(400)
                request.write("No Result found")
            elif isinstance(result, CloudChunk):
                request.setResponseCode(200)
                request.write(result.encode())
            else:
                request.setResponseCode(400)
                request.write(result)
            request.finish()

        msg = json.loads(request.content.read())
        try:
            token = get_and_check_query_token(msg)
            check_query_token_valid(token, self.dhtstorage.max_time_check)
            self.dhtstorage.get_chunk(token).addCallback(respond)
            return NOT_DONE_YET
        except:
            request.setResponseCode(400)
            return "ERROR"
"""
