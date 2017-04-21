import json

from cachetools import TTLCache
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

    def __init__(self, ip='127.0.0.1', port=5000, max_cache_size=1000, ttl_policy=300):
        TalosVCRestClient.__init__(self, ip, port)
        self.pool = HTTPConnectionPool(reactor)
        self.agent = Agent(reactor, pool=self.pool)
        self.policy_cache = TTLCache(max_cache_size, ttl_policy)

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

    def _get_policy_cache(self, owner, streamid):
        try:
            return self.policy_cache["%s%s" % (str(owner), str(streamid))]
        except KeyError:
            return None

    def _put_policy_cache(self, owner, streamid, policy):
        self.policy_cache["%s%s" % (str(owner), str(streamid))] = policy
        self._put_policy_txid_cache(policy.txid, policy)

    def _get_policy_txid_cache(self, txid):
        try:
            return self.policy_cache[txid]
        except KeyError:
            return None

    def _put_policy_txid_cache(self, txid, policy):
        self.policy_cache[txid] = policy
        self._put_policy_cache(policy.owner, policy.stream_id, policy)

    def get_policy(self, owner, streamid):
        cache_polciy = self._get_policy_cache(owner, streamid)
        if cache_polciy is not None:
            return defer.succeed(cache_polciy)

        url = "http://%s:%d/policy?owner=%s&stream-id=%d" % (self.ip, self.port, owner, int(streamid))

        def handle_body(body):
            if body is None:
                raise TalosVCRestClientError("Received reuqest without body")
            policy = create_policy_from_json_str(body)
            self._put_policy_cache(owner, streamid, policy)
            return defer.succeed(policy)

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
        cache_polciy = self._get_policy_txid_cache(txid)
        if cache_polciy is not None:
            return defer.succeed(cache_polciy)

        url = "http://%s:%d/policy?txid=%s" % (self.ip, self.port, txid)

        def handle_body(body):
            if body is None:
                raise TalosVCRestClientError("Received reuqest without body")
            policy = create_policy_from_json_str(body)
            self._put_policy_txid_cache(txid, policy)
            return defer.succeed(policy)

        return self._perform_request(url).addCallback(handle_body)
