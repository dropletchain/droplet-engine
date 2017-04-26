import requests
import cachetools
from cachetools import TTLCache

from talosvc.policy import create_policy_from_json_str


class TalosVCRestClientError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class TalosVCRestClient(object):
    def __init__(self, ip='127.0.0.1', port=5000, max_cache_size=1000, ttl_policy=60):
        self.ip = ip
        self.port = port
        self.policy_cache = TTLCache(max_cache_size, ttl_policy)

    def _get_policy_cache(self, owner, streamid):
        try:
            return self.policy_cache["%s%s" % (str(owner), str(streamid))]
        except KeyError:
            return None

    def _put_policy_cache(self, owner, streamid, policy):
        self.policy_cache["%s%s" % (str(owner), str(streamid))] = policy
        self.policy_cache[policy.txid] = policy

    def _get_policy_txid_cache(self, txid):
        try:
            return self.policy_cache[txid]
        except KeyError:
            return None

    def _put_policy_txid_cache(self, txid, policy):
        self.policy_cache[txid] = policy
        self.policy_cache["%s%s" % (str(policy.owner), str(policy.stream_id))] = policy

    def _check_code(self, code, reason):
        if not code == 200:
            raise TalosVCRestClientError(reason)

    def get_policy(self, owner, streamid, do_cache=True):
        if do_cache:
            cache_polciy = self._get_policy_cache(owner, streamid)
            if cache_polciy is not None:
                return cache_polciy

        req = requests.get("http://%s:%d/policy?owner=%s&stream-id=%d" % (self.ip, self.port, owner, int(streamid)))
        self._check_code(req.status_code, req.reason)
        policy = create_policy_from_json_str(req.text)
        self._put_policy_cache(owner, streamid, policy)
        return policy

    def get_policies_for_owner(self, owner):
        req = requests.get("http://%s:%d/streamids?owner=%s" % (self.ip, self.port, owner))
        self._check_code(req.status_code, req.reason)
        return [int(i) for i in req.json()['stream-ids']]

    def get_owners(self, limit=10, offset=0):
        req = requests.get("http://%s:%d/owners?limit=%d&offset=%d" % (self.ip, self.port, limit, offset))
        self._check_code(req.status_code, req.reason)
        return [str(x) for x in req.json()['owners']]

    def get_policy_with_txid(self, txid, do_cache=True):
        if do_cache:
            cache_polciy = self._get_policy_txid_cache(txid)
            if cache_polciy is not None:
                return cache_polciy

        req = requests.get("http://%s:%d/policy?txid=%s" % (self.ip, self.port, txid))
        self._check_code(req.status_code, req.reason)
        policy = create_policy_from_json_str(req.text)
        self._put_policy_txid_cache(txid, policy)
        return policy
