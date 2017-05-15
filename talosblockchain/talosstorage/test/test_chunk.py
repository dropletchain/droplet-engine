import unittest
import time
import json
from cryptography.exceptions import InvalidSignature, InvalidTag
from cryptography.hazmat.primitives import serialization
from pybitcoin import extract_bin_bitcoin_pubkey, get_bin_hash160, bin_hash160_to_address

from global_tests.test_storage_api import generate_random_chunk
from talosstorage.checks import check_key_matches, check_tag_matches, check_signature, \
    get_crypto_ecdsa_pubkey_from_bitcoin_hex, BitcoinVersionedPrivateKey, get_priv_key, get_bitcoin_address_for_pubkey, \
    BitcoinVersionedPublicKey, QueryToken, check_valid
from talosstorage.chunkdata import *

import talosstorage.keymanagement as km
from timeit import default_timer as timer

from talosstorage.storage import InvalidChunkError, LevelDBStorage
from talosvc.talosclient.restapiclient import TalosVCRestClient

data_chunk_java = """a0828a53567cce1981b35e4560036947bb51dce8bab65f4825fb90168475f1eb000000004ad439ed0fbc7f861e05dd7b7e171192838191418cf7467ee5c0d6290ca178a33f0700000e0a272f4a9bcc17965ce6c747d8e6a5676dee442d22d808c33c04ec00b70134b2cf2601f4626bba19f22ae3917f275ef6ef9b7d2b9c41e0f988d6df5491082a6f5799c325ed01d93810d6c9925e9ad81884f4ea18066837985853c6e1f3f36caf67a8b93e6cbec446a2e4d5d1105c91db111d0f18bf8e03724e268b419461f95c6767c563df5d8c1fd27cc8b86550b2c9b74107e0d7dbc6a2f6c613041d4a558157cfec87ea019263a8ccbce4b26b203839e793362f557d0f7cff6a2861e5eaa0d958ef39df9a61cf74556d65ce73b0b924aa8e5bcfa03f8ec91bbd9cdb3f7c1d8978383fe244b605e38056e0d9e3446625e780a2218e427754794b040d6505d57b35aa8a8e9c35306ca8f9fe877087eed4c4d7658faf85ab43e69463f233146c420a2eae683a988873bf1b6a8c53a776bb96964aa940f20d3616092d4f0567d3d9cce0ea52d99a60c665e42d5a13ee45869ef4e009bb759ddc4c9802434ef81dce51a01af7357787f59a703a5567bc61258768e3389ce17f0e3652a4b8356ffac05a1966609b09b51e8000db39f31d4b4e06c39f25cdc07f7317b6fa7b95e40d9d19f92e3e0590337fbb246f34379f3b2a7e7cdcdb83efff226ef8ed58221a466d835746c744b65ee4800ab8bb4780aad210464733cd3886ba0d3f3b81dd37962d5e6595abf3fc5bb9eafe7f7dc2ea8807e4782f793530d0bfa25865546d50020e17d5f7d4ef3b180e35486780684099b3e33b0d3b623202793a5ec43339a772d06ccbb635fce9e04d967103387f05065088bc8e5907ab35a9138768967ddf951e7c32a3cf2ea444abba28f9c5391a63a8a14e4d6d519db3c2065dad54b6f8a55c89c1bdae59cb8455bce3f292396226f8e270fd1f449659b535bb84430bedaee63ba7be9e9631b6e23775f7e1b034d291a072f375b72af8c700356d32c23312ef9dab374cdb9caaa8926494a96f9f64cc2539e9edb155e7115dc27ee578d25817def371bea369c76e0fa6dc8553a02d7a1c7028663fabe5dac9972ee38170f418362b3854c5c3b9bf945f459f1035eb2a74b45c541f3b9da3631512b5e87716d37c1125873d41f65fe22cd3ecb23c00e8d8f7665b14ce112b6a0e27232a260ea5c91448dd4d7fe4cf104aef0e49e249c0606a48c13d67919adb99cb35594f6580f269d9ff8ec13a06e5085bc153809ea275220a6a2517a77807c45a8eb2a36fcb7f12d82542b3e0c38bd4d07b0abaf5660c7038d75ff0a69565c4a62e2fd23721805e30af15668217d56181ae007f85c42ef728bae8e14f233b1e24f336da9aadbe75dd344cefebcb1f8d785e04358778df7d6a638ad22f861435443dddf9d49bccda7983108b05b01b325598db1c468e9922dfcb86466789f63438a13a8bb044ea948e584e21507590217810432d238c8112e23fb7a1ee41885d5ccb8405ae2aaf28ab64172af20dfb8c61f41c88960a5a62f5a593ee188e000a18ba7071cfbe1ec61ff11c2430e262a51047703309047704f7b957c80460740dc2d8940bda119b64e548c9272338dcefa23bcce39268573509162f0451e1b6c0a598f25aa3b407b960d0028fbd8f37379d28b16aa9b49b0288187ecdfc40b101fc3e12806f0839f68d4687b4cf963108d1c1cfa99ea26c3ae05df91d9f432b0baa1c59207786b509d32b64a224474bcced8b3fd9266ce2acbc74d4551e9240166ab361b6913efb9ffc7f3e842c3be4a7501e38e42e4d516ba0b229229f84b57623def4e7b088843d770e975434a076f6be689d31f962711c20f1e6a163c798d4843540d66618c7db985eb7c5b699b7aaaaa8f253afe06ec7af5cd1a5ea03c1efb347dc4c4a2763c5768943833b7d5898d88675c105c4a362d6dd9dc6f23fcccce12460a11e819855f7e832d7fcd1e3515b1215fe83f6ca38c10c9d0a9659bed5c401086c584032a4a27634130ca4235dd2960e0203ac684ef3096b20bb3fdc63892098e05ab930425af2adfdd435e071f2dbcc80381045f55a913086fe02bb90d033e3868c4ca13dc3525a1dbe701ce28aa9623898677bbf8495fe52751b5f3368dbe769ea6bde558356d36a22400adf30bef36dd8b42afa8fe351760c91bc8e90c3163fd3f3e0fa86381c03224f2e412438e5cf0f440e3711be9ca83d2701cb5f38f6662fa2262652bf407fbad5639aa74a7ba91aff7c1029297218a0ee3069997795ec3dfe6c73b63f106da4f530e6a11e4cf8079194faf814df3e99a7fea6203de02af053578efa1ba7e6d92abb2631994ba1d9cb73f079cd67c6411866a6b39dbce446777ffef37971abbabd579bb62f2d68c4f9b03f50a4ccebbe6f94577e36c512fb2983a1d5d5c0da72072ea7ca3ae9428b6cdd313ee1b1e6f062aa982a50902e4eb36f3ab5bfa90afeed44d9dac707ec341f61df523fb51b78bd41c0f191dbc1973ecc8bf0dd4aeb56b0c71fd8b46fa3dec388c35ba5e049a7648bac3c7d3ca22cfc655084a07019a505825f787a2b92d31dc5b73830e0a6fa1e3a87b59b9bbc641920902e2afd9b7bcb46c3fa4b1c9392b3cad59aafc245c959a6bc003179ac674484234049c32b161a815cd0a0f21139ceea598e534040145a231689a3c4ded152601f13b2f8d842fcd76524418230450221008a5206ca56ffe11381f564012cedd7668e34be5f5e5db3e8360be88b84ce011402206d21456e843618ad967584fa300755148cb9bec6049f1bd2e211fdf34ae9f178"""
data_pub_java =   """a0828a53567cce1981b35e4560036947bb51dce8bab65f4825fb90168475f1eb000000004ad439ed0fbc7f861e05dd7b7e171192838191418cf7467ee5c0d6290ca178a33f0700000e0a272f4a9bcc17965ce6c747d8e6a5676dee442d22d808c33c04ec00b70134b2cf2601f4626bba19f22ae3917f275ef6ef9b7d2b9c41e0f988d6df5491082a6f5799c325ed01d93810d6c9925e9ad81884f4ea18066837985853c6e1f3f36caf67a8b93e6cbec446a2e4d5d1105c91db111d0f18bf8e03724e268b419461f95c6767c563df5d8c1fd27cc8b86550b2c9b74107e0d7dbc6a2f6c613041d4a558157cfec87ea019263a8ccbce4b26b203839e793362f557d0f7cff6a2861e5eaa0d958ef39df9a61cf74556d65ce73b0b924aa8e5bcfa03f8ec91bbd9cdb3f7c1d8978383fe244b605e38056e0d9e3446625e780a2218e427754794b040d6505d57b35aa8a8e9c35306ca8f9fe877087eed4c4d7658faf85ab43e69463f233146c420a2eae683a988873bf1b6a8c53a776bb96964aa940f20d3616092d4f0567d3d9cce0ea52d99a60c665e42d5a13ee45869ef4e009bb759ddc4c9802434ef81dce51a01af7357787f59a703a5567bc61258768e3389ce17f0e3652a4b8356ffac05a1966609b09b51e8000db39f31d4b4e06c39f25cdc07f7317b6fa7b95e40d9d19f92e3e0590337fbb246f34379f3b2a7e7cdcdb83efff226ef8ed58221a466d835746c744b65ee4800ab8bb4780aad210464733cd3886ba0d3f3b81dd37962d5e6595abf3fc5bb9eafe7f7dc2ea8807e4782f793530d0bfa25865546d50020e17d5f7d4ef3b180e35486780684099b3e33b0d3b623202793a5ec43339a772d06ccbb635fce9e04d967103387f05065088bc8e5907ab35a9138768967ddf951e7c32a3cf2ea444abba28f9c5391a63a8a14e4d6d519db3c2065dad54b6f8a55c89c1bdae59cb8455bce3f292396226f8e270fd1f449659b535bb84430bedaee63ba7be9e9631b6e23775f7e1b034d291a072f375b72af8c700356d32c23312ef9dab374cdb9caaa8926494a96f9f64cc2539e9edb155e7115dc27ee578d25817def371bea369c76e0fa6dc8553a02d7a1c7028663fabe5dac9972ee38170f418362b3854c5c3b9bf945f459f1035eb2a74b45c541f3b9da3631512b5e87716d37c1125873d41f65fe22cd3ecb23c00e8d8f7665b14ce112b6a0e27232a260ea5c91448dd4d7fe4cf104aef0e49e249c0606a48c13d67919adb99cb35594f6580f269d9ff8ec13a06e5085bc153809ea275220a6a2517a77807c45a8eb2a36fcb7f12d82542b3e0c38bd4d07b0abaf5660c7038d75ff0a69565c4a62e2fd23721805e30af15668217d56181ae007f85c42ef728bae8e14f233b1e24f336da9aadbe75dd344cefebcb1f8d785e04358778df7d6a638ad22f861435443dddf9d49bccda7983108b05b01b325598db1c468e9922dfcb86466789f63438a13a8bb044ea948e584e21507590217810432d238c8112e23fb7a1ee41885d5ccb8405ae2aaf28ab64172af20dfb8c61f41c88960a5a62f5a593ee188e000a18ba7071cfbe1ec61ff11c2430e262a51047703309047704f7b957c80460740dc2d8940bda119b64e548c9272338dcefa23bcce39268573509162f0451e1b6c0a598f25aa3b407b960d0028fbd8f37379d28b16aa9b49b0288187ecdfc40b101fc3e12806f0839f68d4687b4cf963108d1c1cfa99ea26c3ae05df91d9f432b0baa1c59207786b509d32b64a224474bcced8b3fd9266ce2acbc74d4551e9240166ab361b6913efb9ffc7f3e842c3be4a7501e38e42e4d516ba0b229229f84b57623def4e7b088843d770e975434a076f6be689d31f962711c20f1e6a163c798d4843540d66618c7db985eb7c5b699b7aaaaa8f253afe06ec7af5cd1a5ea03c1efb347dc4c4a2763c5768943833b7d5898d88675c105c4a362d6dd9dc6f23fcccce12460a11e819855f7e832d7fcd1e3515b1215fe83f6ca38c10c9d0a9659bed5c401086c584032a4a27634130ca4235dd2960e0203ac684ef3096b20bb3fdc63892098e05ab930425af2adfdd435e071f2dbcc80381045f55a913086fe02bb90d033e3868c4ca13dc3525a1dbe701ce28aa9623898677bbf8495fe52751b5f3368dbe769ea6bde558356d36a22400adf30bef36dd8b42afa8fe351760c91bc8e90c3163fd3f3e0fa86381c03224f2e412438e5cf0f440e3711be9ca83d2701cb5f38f6662fa2262652bf407fbad5639aa74a7ba91aff7c1029297218a0ee3069997795ec3dfe6c73b63f106da4f530e6a11e4cf8079194faf814df3e99a7fea6203de02af053578efa1ba7e6d92abb2631994ba1d9cb73f079cd67c6411866a6b39dbce446777ffef37971abbabd579bb62f2d68c4f9b03f50a4ccebbe6f94577e36c512fb2983a1d5d5c0da72072ea7ca3ae9428b6cdd313ee1b1e6f062aa982a50902e4eb36f3ab5bfa90afeed44d9dac707ec341f61df523fb51b78bd41c0f191dbc1973ecc8bf0dd4aeb56b0c71fd8b46fa3dec388c35ba5e049a7648bac3c7d3ca22cfc655084a07019a505825f787a2b92d31dc5b73830e0a6fa1e3a87b59b9bbc641920902e2afd9b7bcb46c3fa4b1c9392b3cad59aafc245c959a6bc003179ac674484234049c32b161a815cd0a0f21139ceea598e534040145a231689a3c4ded152601f13b2f8d842fcd765244182"""

class TestChunk(unittest.TestCase):

    def test_chunk1(self):
        chunk = ChunkData()
        for i in range(1000):
            entry = DoubleEntry(int(time.time()), "test", float(i))
            chunk.add_entry(entry)
        key = os.urandom(32)
        private_key = ec.generate_private_key(ec.SECP256K1, default_backend())
        stream_ident = DataStreamIdentifier("pubaddr", 3, "asvcgdterategdts",
                                            "59f7a5a9de7a44ad0f8b0cb95faee0a2a43af1f99ec7cab036b737a4c0f911bb")

        cd = create_cloud_chunk(stream_ident, 1, private_key, 1, key, chunk)
        self.assertTrue(cd.check_signature(private_key.public_key()))
        chunk_after = cd.get_and_check_chunk_data(key)

        for i in range(len(chunk_after.entries)):
            self.assertEquals(str(chunk_after.entries[i]), str(chunk.entries[i]))

        encoded_cloud_chunk = cd.encode()
        print hexlify(encoded_cloud_chunk)
        cloud_chunk_after = CloudChunk.decode(encoded_cloud_chunk)

        self.assertTrue(cloud_chunk_after.check_signature(private_key.public_key()))
        chunk_after = cd.get_and_check_chunk_data(key)

        for i in range(len(chunk_after.entries)):
            self.assertEquals(str(chunk_after.entries[i]), str(chunk.entries[i]))
        encoded_cloud_chunk = list(encoded_cloud_chunk)
        encoded_cloud_chunk[2] = 'x'
        encoded_cloud_chunk = "".join(encoded_cloud_chunk)
        cloud_chunk_after = CloudChunk.decode(encoded_cloud_chunk)

        ok = False
        try:
            cloud_chunk_after.check_signature(private_key.public_key())
        except InvalidSignature:
            ok = True
        self.assertTrue(ok)

        ok = False
        try:
            cloud_chunk_after.get_and_check_chunk_data(key)
        except InvalidTag:
            ok = True
        self.assertTrue(ok)

    def test_picture_entry(self):
        with open("./pylepton/haas.jpg", 'r') as f:
            pic = f.read()
        chunk = ChunkData(entry_type=TYPE_PICTURE_ENTRY)
        for i in range(5):
            entry = PictureEntry(int(time.time()), "haas.jpg", pic)
            chunk.add_entry(entry)
        encoded = chunk.encode()
        chunk_after = ChunkData.decode(encoded)
        self.assertEquals(pic, chunk_after.entries[0].picture_data)


def check_chunk_valid(chunk, policy, chunk_id=None):
    try:
        check_signature(chunk, policy)
    except InvalidSignature:
        raise InvalidChunkError("Chunk key doesn't match")


class MeasureCheck(unittest.TestCase):
    def test_chunk1(self):
        client = TalosVCRestClient()
        for i in range(100):
            chunk = generate_random_chunk(i)
            policy = client.get_policy_with_txid(chunk.get_tag_hex())
            before = timer()
            check_chunk_valid(chunk, policy, chunk_id=i)
            print "Time check %s" % ((timer()-before)*1000,)

    def test_signature(self):
        data = "Hello"*1000

        prv_key = ec.generate_private_key(ec.SECP256K1, default_backend())

        for i in range(100):
            signature = hash_sign_data(prv_key, data)
            before = timer()
            check_signed_data(prv_key.public_key(), signature, data)
            print "Time check %s" % ((timer() - before) * 1000,)

    def test_cross(self):
        client = TalosVCRestClient()
        for i in range(100):
            chunk = generate_random_chunk(i)
            policy = client.get_policy_with_txid(chunk.get_tag_hex())
            before = timer()
            pub_key = get_crypto_ecdsa_pubkey_from_bitcoin_hex(str(policy.owner_pk))
            print "Time check %s" % ((timer() - before) * 1000,)

    def test_storage(self):
        key = BitcoinVersionedPrivateKey("cN5YgNRq8rbcJwngdp3fRzv833E7Z74TsF8nB6GhzRg8Gd9aGWH1")
        talosStorage = LevelDBStorage("db_tmp")
        client = TalosVCRestClient()
        for i in range(100):
            chunk = generate_random_chunk(i)
            policy = client.get_policy_with_txid(chunk.get_tag_hex())
            before = timer()
            talosStorage.store_check_chunk(chunk, i, policy)
            print "Time store %s" % ((timer()-before)*1000,)
            keeper = TimeKeeper()
            before = timer()
            talosStorage.get_check_chunk(chunk.key, key.public_key().to_hex(), policy, time_keeper=keeper)
            print "Time get %s" % ((timer() - before) * 1000,)

        for (key, value) in talosStorage.db.RangeIter():
            print base64.b64encode(key)
            print base64.b64encode(value)

    def check_check_func(self):
        key = BitcoinVersionedPrivateKey("cN5YgNRq8rbcJwngdp3fRzv833E7Z74TsF8nB6GhzRg8Gd9aGWH1")
        client = TalosVCRestClient()
        chunk = generate_random_chunk(1)
        policy = client.get_policy_with_txid(chunk.get_tag_hex())

        def get_bitcoin_address_for_pubkey_tmp(hex_pubkey):
            before = timer()
            priv = extract_bin_bitcoin_pubkey(hex_pubkey)
            hash_priv = get_bin_hash160(priv)
            addr = bin_hash160_to_address(hash_priv, version_byte=111)
            print "Time creation %s" % ((timer() - before) * 1000,)
            return addr

        def check_access_allowed_tmp(hex_pubkey, policy):
            before = timer()
            addr = get_bitcoin_address_for_pubkey_tmp(str(hex_pubkey))
            print "Bitcoin_lib %s" % ((timer() - before) * 1000,)
            if addr == policy.owner:
                return True
            if addr in policy.shares:
                return True
            return False

        self.assertTrue(check_access_allowed_tmp(key.public_key().to_hex(), policy))

    def test_identifier(self):
        ident = DataStreamIdentifier("lubu", 1, "\x00", "lubu")
        print hexlify(ident.get_key_for_blockid(0))

    def test_entry(self):
        entry = DoubleEntry(1, "lubu", 0.55);
        print hexlify(entry.encode())

    def test_chunk_java(self):
        privkey = "cQ1HBRRvJ9DaV2UZsEf5w1uLAoXjSVpLYVH5dB5hZUWk5jeJ8KCL"
        chunk = CloudChunk.decode(unhexlify(data_chunk_java))
        key = BitcoinVersionedPrivateKey(privkey)
        data_pub = chunk.encode_without_signature()
        print hexlify(data_pub)
        print data_pub_java
        print hexlify(data_pub) == data_pub_java
        print chunk.get_key_hex()
        print chunk.get_tag_hex()
        print chunk.check_signature(get_crypto_ecdsa_pubkey_from_bitcoin_hex(key.public_key().to_hex()))

    def test_token_check(self):
        privkey = "cPuiZfHTkWAPhPvMSPetvP1jRarkQ8BRtPrEVuP5PhDsTGrrcm2f"
        dataSign = "64666173646661736661736466647366320000000000000000000000000000000000000000000000000000000000000000"
        tokenS = """{"owner":"dfasdfasfasdfdsf","chunk_key":"AAAAAAAAAAAAAAAAAAAAAA==","stream_id":2,"signature":"MEQCIBtOgOqsBR5K0RQs7MP4ef2oL+ycM9sMklf1OZIdHTH4AiAs+zD8iU5iFQML1OXF9ORFiNwyacF16jMUSTsNoJYXGQ==","nonce":"AAAAAAAAAAAAAAAAAAAAAA==","pubkey":"0222d41a2f7e3fb398cfe320bfcd25712f675c5d916664e3f5132feaecc8a4603f"}"""
        key = BitcoinVersionedPrivateKey(privkey)


        token = QueryToken.from_json(json.loads(tokenS))
        dataSignHere = hexlify(token.get_signature_data())
        print key.to_hex()
        print key.public_key().to_hex()
        print token.pubkey
        print key.public_key().to_hex() == token.pubkey


        print dataSignHere
        print dataSign == dataSignHere

        print "ok?"
        print check_valid(token)

    def test_key_siwtch(self):
        key = BitcoinVersionedPrivateKey("cN5YgNRq8rbcJwngdp3fRzv833E7Z74TsF8nB6GhzRg8Gd9aGWH1")

        def get_priv_key2(bvpk_private_key):
            return serialization.load_pem_private_key(
                bvpk_private_key.to_pem(),
                password=None,
                backend=default_backend())

        other = get_priv_key(key)
        priv2 = get_priv_key2(key)

        def serialize_priv_key(private_key):
            numbers = private_key.private_numbers()
            return '%x' % numbers.private_value
        ser_priv1 = serialize_priv_key(other)
        ser_priv2 = serialize_priv_key(priv2)
        print "%s\n%s" % (ser_priv1, ser_priv2)

        self.assertEquals(serialize_priv_key(other), serialize_priv_key(priv2))
        self.assertEquals(other.private_numbers(), priv2.private_numbers())

        data = "Hello"
        signature1 = hash_sign_data(other, data)
        signature2 = hash_sign_data(priv2, data)

        self.assertTrue(check_signed_data(other.public_key(), signature2, data))
        self.assertTrue(check_signed_data(priv2.public_key(), signature1, data))


class TestKeyReg(unittest.TestCase):

    def test_key_reg(self):
        n = 100
        max_version = 500
        gen = km.KeyRegressionGenerator(seed="hello", n=n)
        key_10, seeda = gen.get_key(max_version-1)
        for i in range(max_version):
            compare = km.KeyRegressionPastGenerator(seeda, key_10, max_version-1, n=n)
            key_null, seed = gen.get_key(i)
            compare_key = compare.get_key(i)
            #print "before: %s after: %s" % (hexlify(key_null), hexlify(compare_key))
            self.assertEquals(compare_key, key_null)

    def test_encode_decode(self):
        n = 100
        gen = km.KeyRegressionGenerator(seed="hello", n=n)
        key, seed = gen.get_key(n*2)
        encoded = km.encode_key(n*2, n, key, seed)
        dn, dversion, dkey, dseed = km.decode_key(encoded)
        #print "before: %s after: %s" % (hexlify(seed), hexlify(dseed))
        self.assertEquals(dn, n*2)
        self.assertEquals(dversion, n)
        self.assertEquals(dkey, key)
        self.assertEquals(dseed, seed)





