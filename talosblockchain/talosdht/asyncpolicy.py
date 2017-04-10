import json
from twisted.internet import reactor, defer
from twisted.web.client import Agent, readBody, HTTPConnectionPool
from twisted.web.http_headers import Headers

from talosvc.policy import create_policy_from_json_str
from talosvc.talosclient.restapiclient import TalosVCRestClient, TalosVCRestClientError


class AsyncPolicyApiClient(TalosVCRestClient):
    """
    Implements the asynchronous version of the policy api client of the virtualchain
    using twisted.
    """
    def __init__(self, ip='127.0.0.1', port=5000):
        TalosVCRestClient.__init__(self, ip, port)
        self.pool = HTTPConnectionPool(reactor)
        self.agent = Agent(reactor, pool=self.pool)

    def _perform_request(self, url):
        d = self.agent.request(
            'GET',
            url,
            Headers({'User-Agent': ['PolicyClient']}),
            None)

        def handle_response(response):
            d = readBody(response)
            if not response.code == 200:
                raise TalosVCRestClientError("No result found")
            return d

        def handle_error(error):
            print error
            raise TalosVCRestClientError("Connection error")

        return d.addCallbacks(handle_response, errback=handle_error)

    def get_policy(self, owner, streamid):
        url = "http://%s:%d/policy?owner=%s&stream-id=%d" % (self.ip, self.port, owner, int(streamid))

        def handle_body(body):
            if body is None:
                raise TalosVCRestClientError("Received reuqest without body")
            return defer.succeed(create_policy_from_json_str(body))
        return self._perform_request(url).addCallback(handle_body)

    def get_policies_for_owner(self, owner):
        url = "http://%s:%d/streamids?owner=%s" % (self.ip, self.port, owner)

        def handle_body(body):
            if body is None:
                raise TalosVCRestClientError("Received reuqest without body")
            json_msg = json.loads(body)
            return defer.succeed([int(i) for i in json_msg['stream-ids']])
        return self._perform_request(url).addCallback(handle_body)

    def get_owners(self, limit=10, offset=0):
        url = "http://%s:%d/owners?limit=%d&offset=%d" % (self.ip, self.port, limit, offset)

        def handle_body(body):
            if body is None:
                raise TalosVCRestClientError("Received reuqest without body")
            json_msg = json.loads(body)
            return defer.succeed([str(x) for x in json_msg['owners']])
        return self._perform_request(url).addCallback(handle_body)

    def get_policy_with_txid(self, txid):
        url = "http://%s:%d/policy?txid=%s" % (self.ip, self.port, txid)

        def handle_body(body):
            if body is None:
                raise TalosVCRestClientError("Received reuqest without body")
            return defer.succeed(create_policy_from_json_str(body))
        return self._perform_request(url).addCallback(handle_body)

