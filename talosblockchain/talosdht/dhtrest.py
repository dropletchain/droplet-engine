import json

from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET

from talosstorage.checks import get_and_check_query_token, check_query_token_valid
from talosstorage.chunkdata import CloudChunk


class AddChunk(Resource):
    allowedMethods = ('POST',)
    def __init__(self, dhtstorage):
        Resource.__init__(self)
        self.dhtstorage = dhtstorage

    def render_POST(self, request):
        def respond(result):
            if result:
                request.setResponseCode(200)
                request.write("OK")
            else:
                request.setResponseCode(400)
                request.write("ERROR")
            request.finish()
        encoded_chunk = request.content.read()
        try:
            chunk = CloudChunk.decode(encoded_chunk)
            self.dhtstorage.store_chunk(chunk).addCallback(respond)
            return NOT_DONE_YET
        except:
            request.setResponseCode(400)
            return "ERROR"


class GetChunk(Resource):
    allowedMethods = ('POST',)

    def __init__(self, dhtstorage):
        Resource.__init__(self)
        self.dhtstorage = dhtstorage

    def render_POST(self, request):
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

