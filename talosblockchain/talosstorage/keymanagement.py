#© 2017-2020, ETH Zurich, D-INFK, lubu@inf.ethz.ch

import hashlib
import os
import struct

from talosstorage.checks import BitcoinVersionedPublicKey


def hash_sha256(to_hash):
    return hashlib.sha256(to_hash).digest()


def hash_sha384_32(to_hash):
    return hashlib.sha384(to_hash).digest()[:32]


class KeyRegressionGenerator:
    def __init__(self, seed=None, n=100, hf_seeds=hash_sha384_32, hf_hashes=hash_sha256):
        self.n = n
        self.hf_seeds = hf_seeds
        self.hf_hashes = hf_hashes
        if seed is None:
            seed = os.urandom(32)
        self.seeds = []
        prev = seed
        for i in range(n):
            prev = hf_seeds(prev)
            self.seeds.append(prev)

    def num_keys(self):
        return self.n * self.n

    def _get_gobal_key_version(self, local_seed_version, local_key_version):
        return self.num_keys() - (local_seed_version * self.n + local_key_version)

    def _get_seed_and_key_for_version(self, key_version):
        local_key_version = (self.num_keys() - 1 - key_version) % self.n
        local_seed_version = (self.num_keys() - 1 - key_version) / self.n
        return local_seed_version, local_key_version

    def get_key(self, key_version):
        ls, lk = self._get_seed_and_key_for_version(key_version)
        local_seed = self.seeds[ls]
        cur_hash = local_seed
        for i in range(lk + 1):
            cur_hash = self.hf_hashes(cur_hash)
            # print "%d, %s" % (i, hexlify(cur_hash))

        seed = None
        if ls + 1 < len(self.seeds):
            seed = self.seeds[ls + 1]
        return cur_hash, seed


class KeyRegressionPastGenerator:
    def __init__(self, seed, key, key_version, n=100, seed_hf=hash_sha384_32, key_hf=hash_sha256):
        self.n = n
        self.seed_hf = seed_hf
        self.key_hf = key_hf
        self.hashes = [key]
        self.cur_seed = seed
        self.ini_version = key_version
        self.cur_version = key_version

    def gen_keys(self, to_version):
        cur_version = self.cur_version
        assert to_version >= 0
        cur_hash = self.hashes[self.ini_version - cur_version]
        while cur_version > to_version:
            cur_version -= 1
            if cur_version % self.n == (self.n - 1):
                cur_hash = self.key_hf(self.cur_seed)
                # print "%d, %s" % (cur_version, hexlify(cur_hash))
                self.cur_seed = self.seed_hf(self.cur_seed)
            else:
                cur_hash = self.key_hf(cur_hash)
            self.hashes.append(cur_hash)
        self.cur_version = cur_version

    def get_key(self, key_version):
        if key_version > self.ini_version:
            raise RuntimeError("cannot support version %d" % key_version)
        if self.cur_version > key_version:
            self.gen_keys(key_version)
        return self.hashes[self.ini_version - key_version]


def encode_key(key_version, n, key, seed):
    assert len(key) == 32, len(seed) == 32
    if seed is None:
        return struct.pack("II", key_version, n) + key
    else:
        return struct.pack("II", key_version, n) + key + seed


def decode_key(encoded_key):
    key = encoded_key
    len_struct = struct.calcsize("II")
    key_version, n = struct.unpack("II", key[:len_struct])
    key_final = key[len_struct:(len_struct + 32)]
    len_struct += 32
    seed = None
    if len(key) > len_struct:
        seed = key[len_struct:(len_struct + 32)]
    return key_version, n, key_final, seed


class IntervalKeyRegression(object):
    def __init__(self, seed1=os.urandom(32), seed2=os.urandom(32), n=1000,
                 hash_func1=hash_sha256, hash_func2=hash_sha384_32):
        self.seed1 = seed1
        self.seed2 = seed2
        self.num_keys = n
        self.range_right = [hash_func1(self.seed1)]
        self.range_left = [hash_func1(self.seed2)]
        self.hash_1 = hash_func1
        self.hash_2 = hash_func2

    def _compute_hash(self, i, l_hashes):
        idx = len(l_hashes) - 1
        if i <= idx:
            return l_hashes[idx]
        while idx < i:
            l_hashes.append(self.hash_1(l_hashes[idx]))
            idx = idx + 1
        return l_hashes[i]

    def get_key_with_version(self, version):
        r_hash = self._compute_hash(version, self.range_right)
        idx_left = self.num_keys - 1 - version
        l_hash = self._compute_hash(idx_left, self.range_left)
        return self.hash_2(r_hash + l_hash)


class KeyShareStorage:
    def __init__(self, to_share_key, pubkeys=[]):
        self.to_share_key = to_share_key
        self.pubkeys = pubkeys

    def add_pubkey(self, pk):
        self.pubkeys.append(pk)

    def remove_pubkey(self, pk):
        self.pubkeys.remove(pk)

    def generate_storage(self, policy_tag):
        """
        Encoding:
        policy tag | num_keys (1 byte) | k1hash160 | lenEnc | ENCpk(key) ..... | signature owner 
        :param policy_tag: 
        :return: 
        """
        assert len(policy_tag) == 32
        data = policy_tag
        for key in self.pubkeys:
            bc_key = BitcoinVersionedPublicKey(key)
            data += bc_key.hash160()
            # use ec-el gamal?
