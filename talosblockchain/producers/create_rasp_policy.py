import ConfigParser
import base64

from pybitcoin import BitcoindClient

from talosvc.config import BitcoinVersionedPrivateKey
from talosvc.talosclient.policycreation import BitcoinPolicyCreator

ip = "46.101.113.112"
timestamp_start = 1497225600
interval = 7200
share = "cT3GKi6SbCwKEG2o9BJCtrmaCDSkAFfvF6nwS3GDb4xbCNBiUoy6"

if __name__ == "__main__":
    config = ConfigParser.RawConfigParser(allow_no_value=False)
    config.read("./config")
    private_key_hex = config.get("raspberry", "PRIVATE_KEY")
    policy_nonce = config.get("raspberry", "NONCE")
    stream_id = config.get("raspberry", "STREAMID")

    private_key = BitcoinVersionedPrivateKey(private_key_hex)
    print private_key.public_key().address()
    share_key = BitcoinVersionedPrivateKey(share)
    client = BitcoindClient("talos", "talos", port=18332, version_byte=111)

    policy_client = BitcoinPolicyCreator(client, private_key)

    policy_client.create_policy(1, int(stream_id), timestamp_start, interval, base64.b64decode(policy_nonce))

    policy_client.add_share_to_policy(int(stream_id), [share_key.public_key().address()])