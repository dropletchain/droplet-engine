import unittest

from talosvc.policy import Policy
from talosvc.config import *


class TestPolicy(unittest.TestCase):

    def test_1(self):
        policy = Policy("Me", 12, 1, "nonce")
        policy.add_share(["A", "B"])
        policy.add_time_interval(12, 3)
        print policy.to_json()
        res = """{"_start_points": [12], "_shares": ["A", "B"], "_intervals": [12]
        , "_version": 1, "_owner": "Me", "_stream_id": 12, "_nonce": "nonce"}"""
        self.assertEquals(res, policy.to_json())


class TestRandom(unittest.TestCase):

    def test_rand(self):
        str = get_policy_cmd_create_str(1, 12, 13, 24, "ABDGFHDTARSGDTSF")
        res = parse_policy_cmd_create_data(str[3:])
        print res