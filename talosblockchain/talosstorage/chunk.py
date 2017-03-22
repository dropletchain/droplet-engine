import struct
import zlib
import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec




class Entry(object):
    def encode(self):
        pass

    def decode(self):
        pass

    def get_encoded_size(self):
        pass


class DoubleEntry(Entry):
    def __init__(self, timestamp, metadata, value):
        self._timestamp = timestamp
        self._metadata = metadata
        self._value = value
        Entry.__init__(self)

    def get_timestamp(self):
        return self._timestamp

    def get_metadata(self):
        return self._metadata

    def get_value(self):
        return self._value

    def get_encoded_size(self):
        return struct.calcsize("IQ") + len(self._metadata) + struct.calcsize("d")

    def encode(self):
        total_size = self.get_encoded_size()
        return struct.pack("IQ", total_size, self._timestamp) + self._metadata + struct.pack("d", self._value)

    def __str__(self):
        return "%s %s %s" % (str(self._timestamp), self._metadata, str(self._value))

    @staticmethod
    def decode(encoded):
        len_struct = struct.calcsize("IQ")
        len_tot, timestamp = struct.unpack("IQ", encoded[:len_struct])
        len_meta = len_tot - len_struct - struct.calcsize("d")
        metadata = encoded[len_struct:(len_struct+len_meta)]
        value, = struct.unpack("d", encoded[(len_struct+len_meta):])
        return DoubleEntry(timestamp, metadata, value)


class Chunk:
    def __init__(self, entries=[], max_size=1000):
        self.entries = entries
        self.max_size = max_size

    def add_entry(self, entry):
        if len(self.entries) >= self.max_size:
            return False
        self.entries.append(entry)
        return True

    def num_entries(self):
        return len(self.entries)

    def remaining_space(self):
        return self.max_size - len(self.entries)

    def encode(self):
        res = ""
        for entry in self.entries:
            res += entry.encode()
        return res

    @staticmethod
    def decode(encoded, entry_decoder=DoubleEntry.decode):
        """
        Assumes |len_entry (4 byte)|encoded entry|
        """
        len_encoded = len(encoded)
        len_integer = struct.calcsize("I")
        cur_pos = 0
        entries = []
        while cur_pos < len_encoded:
            len_entry, = struct.unpack("I", encoded[cur_pos:(cur_pos+len_integer)])
            entries.append(entry_decoder(encoded[cur_pos:(cur_pos+len_entry)]))
            cur_pos += len_entry
        return Chunk(entries=entries, max_size=len(entries))


def compress_data(data, level=6):
    return zlib.compress(data, level)


def decompress_data(data):
    return zlib.decompress(data)


def encrypt_aes_gcm_data(key, data):
    iv = os.urandom(12)
    encryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv),
        backend=default_backend()
    ).encryptor()
    ciphertext = encryptor.update(data) + encryptor.finalize()
    return struct.pack("B", len(encryptor.tag)) + iv + encryptor.tag + ciphertext


def decrypt_aes_gcm_data(key, data):
    len, = struct.unpack("B", data[0])
    iv = data[1:13]
    tag = data[13:(13+len)]
    ciphertext = data[(13+len):]

    decryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv, tag),
        backend=default_backend()
    ).decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()


def hash_sign_data(private_key, data):
    signer = private_key.signer(ec.ECDSA(hashes.SHA256()))
    signer.update(data)
    signiture = signer.finalize()
    return struct.pack("B", len(signiture)) + signiture + data


def check_and_unpack_hash_sign_data(public_key, data):
    len_signature, = struct.unpack("B", data[0])
    signature = data[1:(1+len_signature)]
    data = data[(1+len_signature):]
    verifier = public_key.verifier(signature, ec.ECDSA(hashes.SHA256()))
    verifier.update(data)
    return data, verifier.verify()
