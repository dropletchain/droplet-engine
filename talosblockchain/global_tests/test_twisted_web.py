#© 2017-2020, ETH Zurich, D-INFK, lubu@inf.ethz.ch

from twisted.internet import reactor
from twisted.web.client import Agent
from twisted.web.http_headers import Headers
from twisted.web.resource import Resource
from twisted.web.server import Site


class Dummy(Resource):
    allowedMethods = ('GET',)

    def __init__(self):
        Resource.__init__(self)

    def getChild(self, path, request):
        return self

    def render_GET(self, request):
        res = " "
        for x in request.prepath:
            res += ":%s:"% x
        return res

root = Resource()
root.putChild("dummy", Dummy())

factory = Site(root)
reactor.listenTCP(12000, factory)

agent = Agent(reactor)

def ok(req, hello):
    print "ok"

d = agent.request(
    'GET',
    'http://%s:%d/dummy' % ('127.0.0.1', 12000),
    Headers({'User-Agent': ['TalosDHTNode']}),
    None)
d.addCallback(ok, "hello")


reactor.run()
