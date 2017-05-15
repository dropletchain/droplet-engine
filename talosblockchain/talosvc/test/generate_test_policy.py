import time
import os

from pybitcoin import BitcoinPrivateKey, BitcoindClient

from talosvc.talosclient.policycreation import BitcoinPolicyCreator



class BitcoinTestnetPrivateKey(BitcoinPrivateKey):
    _pubkeyhash_version_byte = 111

#private_key_hex = 'cQ9BsS11H7UaRTDz5cS8H7L2pV57zEjXe7aC2A7dRNatDhkhrEDb'
private_key_hex = 'cQ1HBRRvJ9DaV2UZsEf5w1uLAoXjSVpLYVH5dB5hZUWk5jeJ8KCL'
private_key = BitcoinTestnetPrivateKey(private_key_hex)
client = BitcoindClient("talos", "talos", port=18332, version_byte=111)

policy_client = BitcoinPolicyCreator(client, private_key)

"""
clinetA = "mm6T8ASEjVW7TeYLmNqwepzM5u35xkyTEX"
clinetB = "mpv24EBXgasKjBmuRHQp734oyC7vbTE1EA"
clinetC = "mx6naH8SFmefgMnWuCft979tLBufRyX528"
"""

clinetA = "mtuVSpDMrtZi5GfZgEJbdR5dSD3ULsQ81y"
clinetB = "muVo7RrtrAP8XPGvombhs7DxN1diBx3P5v"
clinetC = "mwNCMtCiaNi6NxnU6yK1uiCwP7vGZzAXjS"

timestamp = int(time.time())
interval = 86400
nonce = "asdfgcbfndhstdzf"

max_streams = 3

for stream_id in range(1, max_streams+1):
    policy_client.create_policy(1 , stream_id, timestamp, interval, os.urandom(16))
    client.bitcoind.generate(1)
    print "Create Policy Stream-id %d" % (stream_id, )

time.sleep(1)
print "Policy write done "

for stream_id in range(1, max_streams+1):
    policy_client.add_share_to_policy(stream_id, [clinetA])
    client.bitcoind.generate(1)
    print "AddShare Stream-id %d, %s" % (stream_id, clinetA)
    time.sleep(1)

for stream_id in range(1, max_streams+1):
    policy_client.add_share_to_policy(stream_id, [clinetC])
    client.bitcoind.generate(1)
    print "AddShare Stream-id %d, %s" % (stream_id, clinetC)
    time.sleep(1)


for stream_id in range(1, 2):
    var = int(time.time())
    policy_client.change_interval_in_policy(stream_id,var, interval/2)
    print "Change Interval Stream-id %d, %s, %s" % (stream_id, str(var), str(interval/2))
    client.bitcoind.generate(1)
    time.sleep(1)

for stream_id in range(1, 2):
    policy_client.remove_share_from_policy(stream_id, [clinetC])
    print "Remove Client Stream-id %d, %s" % (stream_id, clinetC)
    client.bitcoind.generate(1)

policy_client.invalidate_policy(2)
client.bitcoind.generate(1)

print "Policy share done "