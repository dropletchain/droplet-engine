import base64
import hashlib
import struct
import zlib
from binascii import unhexlify, hexlify

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from pylepton.lepton import *
from talosstorage.timebench import TimeKeeper

"""
Implementaion of the chunks, each stream is partitioned into chunks.
"""


def compress_data(data, level=6):
    """
    Compresses the data wit zlib
    :param data: the data
    :param level: compresssion level
    :return: 
    """
    return zlib.compress(data, level)


def decompress_data(data):
    """
    Decompresses the data with zlib
    :param data: 
    :return: 
    """
    return zlib.decompress(data)


def encrypt_aes_gcm_data(key, plain_data, data):
    """
    Encrypts the data with aes in gcm mode (conf + auth)
    :param key: the 32 byte encryption key
    :param plain_data: the which should be authenticated but not encrypted
    :param data: the data to encrypt
    :return: ciphertext
    """
    iv = os.urandom(12)
    encryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv),
        backend=default_backend()
    ).encryptor()
    encryptor.authenticate_additional_data(plain_data)
    ciphertext = encryptor.update(data) + encryptor.finalize()
    return iv + ciphertext, encryptor.tag


def decrypt_aes_gcm_data(key, tag, plain_data, data):
    """
    Decrypts a ciphertext and checks the tag with aes gcm.
    :param key: the 32 byte decryption key
    :param tag: the authentication tag
    :param plain_data: the plaint data to be authenticated
    :param data: the ciphertext
    :return: plaintext (throws InvalidTag exception if auth fails)
    """
    iv = data[0:12]
    ciphertext = data[12:]

    decryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv, tag),
        backend=default_backend()
    ).decryptor()
    decryptor.authenticate_additional_data(plain_data)
    return decryptor.update(ciphertext) + decryptor.finalize()


def hash_sign_data(private_key, data):
    """
    Given the private key signs the data with ECDSA-SHA256
    :param private_key: the private key (crypthography framework object)
    :param data: the data to be signed
    :return: the signature
    """
    signer = private_key.signer(ec.ECDSA(hashes.SHA256()))
    signer.update(data)
    return signer.finalize()


def check_signed_data(public_key, signature, data):
    """
    Checks if the given signature matches the data with ECDSA-SHA256
    :param public_key: the public key (crypthography framework object)
    :param signature: the signature
    :param data: the data
    :return: True if ok else throws InvalidSignature exception 
    """
    verifier = public_key.verifier(signature, ec.ECDSA(hashes.SHA256()))
    verifier.update(data)
    return verifier.verify()


TYPE_DOUBLE_ENTRY = 0
TYPE_MULTI_DOUBLE_ENTRY = 2
TYPE_MULTI_INT_ENTRY = 3
TYPE_PICTURE_ENTRY = 1


class Entry(object):
    """
    Represents a key value entry in a chunk
    """

    def get_type_id(self):
        pass

    def encode(self, use_compression=False):
        pass

    def decode(self, use_compression):
        pass

    def get_encoded_size(self):
        pass


class PictureEntry(Entry):
    """
    Represents an Entry containing an image 
    """
    def __init__(self, timestamp, metadata, picture_jpg_data, time_keeper=TimeKeeper()):
        """
        Create a picture entry
        :param timestamp: (int) unix timestamp
        :param metadata: string metadata
        :param picture_jpg_data: the picture as bytes
        :param time_keeper: for benchmarking
        """
        self.timestamp = timestamp
        self.metadata = metadata
        self.picture_data = picture_jpg_data
        self.time_keeper = time_keeper
        Entry.__init__(self)

    def get_type_id(self):
        return TYPE_PICTURE_ENTRY

    def get_encoded_size(self):
        return struct.calcsize("<IBQI") + len(self.metadata) + len(self.picture_data)

    def get_encoded_size_compressed(self, compressed_len):
        return struct.calcsize("<IBQI") + len(self.metadata) + compressed_len

    def encode(self, use_compression=True):
        if use_compression:
            self.time_keeper.start_clock()
            compressed_picture = compress_jpg_data(self.picture_data)
            self.time_keeper.stop_clock("time_lepton_compression")
            total_size = self.get_encoded_size_compressed(len(compressed_picture))
        else:
            compressed_picture = self.picture_data
            total_size = self.get_encoded_size_compressed(len(compressed_picture))
        return struct.pack("<IBQI", total_size, self.get_type_id(), self.timestamp, len(self.metadata)) + self.metadata + compressed_picture

    def __str__(self):
        return "%s %s" % (str(self.timestamp), self.metadata)

    @staticmethod
    def decode(encoded, use_decompression=True):
        len_struct = struct.calcsize("<IBQI")
        len_tot, _, timestamp, len_meta = struct.unpack("<IBQI", encoded[:len_struct])
        metadata = encoded[len_struct:(len_struct + len_meta)]
        value = encoded[(len_struct + len_meta):]
        if use_decompression:
            decompressed_data = decompress_jpg_data(value)
        else:
            decompressed_data = value
        return PictureEntry(timestamp, metadata, decompressed_data)


class DoubleEntry(Entry):
    """
    Represents a entry with a double value.
    E.x. a sensor value
    """
    def __init__(self, timestamp, metadata, value):
        """
        Create a double entry
        :param timestamp: (int) unix timestamp
        :param metadata: string metadata
        :param value: the value as double
        """
        self.timestamp = timestamp
        self.metadata = metadata
        self.value = value
        Entry.__init__(self)

    def get_type_id(self):
        return TYPE_DOUBLE_ENTRY

    def get_encoded_size(self):
        return struct.calcsize("<IBQ") + len(self.metadata) + struct.calcsize("d")

    def encode(self, use_compression=False):
        total_size = self.get_encoded_size()
        return struct.pack("<IBQ", total_size, self.get_type_id(), self.timestamp) + self.metadata + struct.pack("d", self.value)

    def __str__(self):
        return "%s %s %s" % (str(self.timestamp), self.metadata, str(self.value))

    @staticmethod
    def decode(encoded, use_compression=False):
        len_struct = struct.calcsize("<IBQ")
        len_tot, _, timestamp = struct.unpack("<IBQ", encoded[:len_struct])
        len_meta = len_tot - len_struct - struct.calcsize("d")
        metadata = encoded[len_struct:(len_struct + len_meta)]
        value, = struct.unpack("d", encoded[(len_struct + len_meta):])
        return DoubleEntry(timestamp, metadata, value)


class MultiDoubleEntry(Entry):
    def __init__(self, timestamp, metadata, values):
        self.timestamp = timestamp
        self.metadata = metadata
        self.values = values
        Entry.__init__(self)

    def get_type_id(self):
        return TYPE_MULTI_DOUBLE_ENTRY

    def get_encoded_size(self):
        return struct.calcsize("<IBQI") + len(self.metadata) + (struct.calcsize("d")*len(self.values))

    def encode(self, use_compression=False):
        total_size = self.get_encoded_size()
        temp = struct.pack("<IBQI", total_size, self.get_type_id(), self.timestamp, len(self.metadata)) + self.metadata
        for value in self.values:
            temp += struct.pack("d", value)
        return temp

    def __str__(self):
        return "%s %s %s" % (str(self.timestamp), self.metadata, str(self.values))

    @staticmethod
    def decode(encoded, use_compression=False):
        len_struct = struct.calcsize("<IBQI")
        len_tot, _, timestamp, len_meta = struct.unpack("<IBQI", encoded[:len_struct])
        size_double = struct.calcsize("d")
        num_double = (len_tot - len_struct - len_meta) / size_double
        metadata = encoded[len_struct:(len_struct + len_meta)]
        tmp = len_struct + len_meta
        values = [struct.unpack("d", encoded[(tmp + i * size_double):(tmp + (i + 1) * size_double)]) for i in range(num_double)]
        return MultiDoubleEntry(timestamp, metadata, values)


class MultiIntegerEntry(Entry):
    def __init__(self, timestamp, metadata, values):
        self.timestamp = timestamp
        self.metadata = metadata
        self.values = values
        Entry.__init__(self)

    def get_type_id(self):
        return TYPE_MULTI_INT_ENTRY

    def get_encoded_size(self):
        return struct.calcsize("<IBQI") + len(self.metadata) + (struct.calcsize("H")*len(self.values))

    def encode(self, use_compression=False):
        total_size = self.get_encoded_size()
        temp = struct.pack("<IBQI", total_size, self.get_type_id(), self.timestamp, len(self.metadata)) + self.metadata
        for value in self.values:
            temp += struct.pack("I", value)
        return temp

    def __str__(self):
        return "%s %s %s" % (str(self.timestamp), self.metadata, str(self.values))

    @staticmethod
    def decode(encoded, use_compression=False):
        len_struct = struct.calcsize("<IBQI")
        len_tot, _, timestamp, len_meta = struct.unpack("<IBQI", encoded[:len_struct])
        size_double = struct.calcsize("I")
        num_double = (len_tot - len_struct - len_meta) / size_double
        metadata = encoded[len_struct:(len_struct + len_meta)]
        tmp = len_struct + len_meta
        values = [struct.unpack("I", encoded[(tmp + i * size_double):(tmp + (i + 1) * size_double)]) for i in range(num_double)]
        return MultiDoubleEntry(timestamp, metadata, values)

DECODER_FOR_TYPE = {
    TYPE_DOUBLE_ENTRY: DoubleEntry.decode,
    TYPE_PICTURE_ENTRY: PictureEntry.decode,
    TYPE_MULTI_DOUBLE_ENTRY: MultiDoubleEntry.decode,
    TYPE_MULTI_INT_ENTRY: MultiIntegerEntry.decode
}


class ChunkData:
    """
    Represents a plaintext chunk. 
    Contains a certain number of entries.
    """
    def __init__(self, entries_in=None, max_size=1000):
        """
        Create a new chunk
        :param entries_in: a list of entries if None create a empry one
        :param max_size: the maximum number of entries
        :param entry_type: the type of entries 
        """
        self.entries = entries_in or []
        self.max_size = max_size

    def add_entry(self, entry):
        """
        Add an entry to the chunk
        :param entry: the entry
        :return: True if success else False i.e. chunk full
        """
        assert entry.get_type_id() == self.type
        if len(self.entries) >= self.max_size:
            return False
        self.entries.append(entry)
        return True

    def num_entries(self):
        return len(self.entries)

    def __iter__(self):
        for x in self.entries:
            yield x

    def remaining_space(self):
        return self.max_size - len(self.entries)

    def encode(self, use_compression=True):
        res = ""
        for entry in self.entries:
            res += entry.encode(use_compression=use_compression)
        return res

    @staticmethod
    def decode(encoded, use_compression=True):
        """
        Assumes: |len_entry (4 byte)| type | encoded entry|
        """
        len_encoded = len(encoded)
        len_integer = struct.calcsize("<IB")
        cur_pos = 0
        entries = []
        while cur_pos < len_encoded:
            len_entry, type_entry = struct.unpack("<IB", encoded[cur_pos:(cur_pos + len_integer)])
            entry_decoder = DECODER_FOR_TYPE[int(type_entry)]
            entries.append(entry_decoder(encoded[cur_pos:(cur_pos + len_entry)], use_compression))
            cur_pos += len_entry
        return ChunkData(entries_in=entries, max_size=len(entries))


class DataStreamIdentifier:
    """
    A helper object for identifying a stream with the policy
    """
    def __init__(self, owner, streamid, nonce, txid_create_policy):
        """
        Create a stream identfier
        :param owner: the owner as (bitcoin address) hex string
        :param streamid: the integer streamid
        :param nonce: the nonce from the polciy as bin
        :param txid_create_policy: the transaction id of the policy as hex string
        """
        self.owner = owner
        self.streamid = streamid
        self.nonce = nonce
        self.txid_create_policy = txid_create_policy

    def get_tag(self):
        return unhexlify(self.txid_create_policy)

    def get_key_for_blockid(self, block_id):
        hasher = hashlib.sha256()
        hasher.update(self.owner)
        hasher.update(str(self.streamid))
        hasher.update(self.nonce)
        hasher.update(str(block_id))
        return hasher.digest()


HASH_BYTES = 32
VERSION_BYTES = 4
MAC_BYTES = 16

def _encode_cloud_chunk_public_part(lookup_key, key_version, policy_tag):
    return lookup_key + struct.pack("<I", key_version) + policy_tag


def _enocde_cloud_chunk_without_signature(lookup_key, key_version, policy_tag, encrypted_data, mac_tag):
    return _encode_cloud_chunk_public_part(lookup_key, key_version, policy_tag) + \
           struct.pack("<I", len(encrypted_data)) + encrypted_data + \
           mac_tag


class CloudChunkDecodingError(Exception):
    def __init__(self, encoded_chunk, msg):
        self.encoded_chunk = encoded_chunk
        self.msg = msg

    def __str__(self):
        return "%s Data: %s " % (repr(self.msg), base64.b64encode(self.encoded_chunk))


class CloudChunk:
    """
        Represents an encrypted and packed chunk.
        
        Format:
        Key = H(Owner-addr  Stream-id  nonce  blockid) 32 bytes
        Symmetric Key-Version (to know which key version to use ) 4 bytes
        Policy-TAG = Create_txt_id
        Len-Chunk + Encrypted Chunk (symmetric Key Ki) X bytes
        MAC (symmetric Key Ki) 16 bytes
        Signature (Public-Key of Owner) X bytes
    """

    def __init__(self, lookup_key, key_version, policy_tag, encrypted_data, mac_tag, signature):
        self.key = lookup_key
        self.key_version = key_version
        self.policy_tag = policy_tag
        self.encrypted_data = encrypted_data
        self.mac_tag = mac_tag
        self.signature = signature

    def get_and_check_chunk_data(self, symmetric_key, compression_used=True, time_keeper=TimeKeeper()):
        """
        Given the symetric key, decrypt + check the data with aes gcm and decompress it 
        :param time_keeper: benchmark 
        :param symmetric_key: the 32 byte key
        :param compression_used: indicates if decompression should be applied
        :return: a ChunkData object, else expcetion thrown 
        """
        pub_part = _encode_cloud_chunk_public_part(self.key, self.key_version, self.policy_tag)
        time_keeper.start_clock()
        data = decrypt_aes_gcm_data(symmetric_key, self.mac_tag, pub_part, self.encrypted_data)
        time_keeper.stop_clock("aes_gcm_decrypt")
        if compression_used:
            time_keeper.start_clock()
            data = decompress_data(data)
            time_keeper.stop_clock("zlib_decompression")
        return ChunkData.decode(data)

    def check_signature(self, public_key):
        """
        Checks if the chunk has a valid signature given the public key
        :param public_key: public key (cryptography lib key format)
        :return: True if ok else throw InvalidSignature exception
        """
        data = _enocde_cloud_chunk_without_signature(self.key, self.key_version,
                                                     self.policy_tag, self.encrypted_data, self.mac_tag)
        return check_signed_data(public_key, self.signature, data)

    def get_encoded_len(self):
        return struct.calcsize("<I") + 2 * HASH_BYTES + VERSION_BYTES + MAC_BYTES + \
               len(self.signature) + len(self.encrypted_data)

    def encode(self):
        return _enocde_cloud_chunk_without_signature(self.key, self.key_version,
                                                     self.policy_tag, self.encrypted_data, self.mac_tag) \
               + self.signature

    def encode_without_signature(self):
        return _enocde_cloud_chunk_without_signature(self.key, self.key_version,
                                                     self.policy_tag, self.encrypted_data, self.mac_tag)

    def get_encoded_without_key(self):
        return self.encode()[HASH_BYTES:]

    def get_tag_hex(self):
        return hexlify(self.policy_tag)

    def get_key_hex(self):
        return hexlify(self.key)

    def get_base64_encoded(self):
        return base64.b64encode(self.encode())

    @staticmethod
    def decode(encoded):
        try:
            encoded = bytes(encoded)
            cur_pos = 0
            len_int = struct.calcsize("<I")
            key = encoded[:HASH_BYTES]
            cur_pos += HASH_BYTES
            key_version, = struct.unpack("<I", encoded[cur_pos:(cur_pos + VERSION_BYTES)])
            cur_pos += VERSION_BYTES
            policy_tag = encoded[cur_pos:(cur_pos + HASH_BYTES)]
            cur_pos += HASH_BYTES
            enc_len, = struct.unpack("<I", encoded[cur_pos:(cur_pos + len_int)])
            cur_pos += len_int
            encrypted_data = encoded[cur_pos:(cur_pos + enc_len)]
            cur_pos += enc_len
            mac_tag = encoded[cur_pos:(cur_pos + MAC_BYTES)]
            cur_pos += MAC_BYTES
            signature = encoded[cur_pos:]
            return CloudChunk(key, key_version, policy_tag, encrypted_data, mac_tag, signature)
        except Exception as r:
            raise CloudChunkDecodingError(encoded, r.message)

    @staticmethod
    def decode_base64_str(encoded):
        return CloudChunk.decode(base64.b64decode(encoded))


def create_cloud_chunk(data_stream_identifier, block_id, private_key, key_version,
                       symmetric_key, chunk_data, use_compression=True, time_keeper=TimeKeeper()):
    """
    Creates a CloudChunk object given a plain ChunkData object. Performs encryption and signing given the keys
    and the stream identifier
    :param data_stream_identifier: a stream identifier object
    :param block_id: the id of the chunk
    :param private_key: the private key (cryptography lib key format)
    :param key_version: the version of the symmetric key
    :param symmetric_key: the 32 byte symmetric key
    :param chunk_data: the ChunkData object
    :param use_compression: indicates if compression sould be apllied default:True
    :param time_keeper: benchmark util object
    :return: a CloudChunk object
    """

    # encode the chunk data
    data = chunk_data.encode()

    # compress it
    if use_compression:
        time_keeper.start_clock()
        data = compress_data(data)
        time_keeper.stop_clock('chunk_compression')
    # get the key for the chunk given the block id
    block_key = data_stream_identifier.get_key_for_blockid(block_id)
    # get the tag for binding the chunk to a policy
    tag = data_stream_identifier.get_tag()

    time_keeper.start_clock()
    # encrypt it with aes gcm
    encrypted_data, mac_tag = encrypt_aes_gcm_data(symmetric_key,
                                                   _encode_cloud_chunk_public_part(block_key, key_version, tag), data)
    time_keeper.stop_clock('gcm_encryption')

    time_keeper.start_clock()
    # sign it with ECDSA-SHA256
    signature = hash_sign_data(private_key,
                               _enocde_cloud_chunk_without_signature(block_key, key_version,
                                                                     tag, encrypted_data, mac_tag))
    time_keeper.stop_clock('ecdsa_signature')
    return CloudChunk(block_key, key_version, tag, encrypted_data, mac_tag, signature)


def get_chunk_data_from_cloud_chunk(cloud_chunk, symmetric_key, is_compressed=True):
    """
    Given an encrypted CloudChunk object, decrypts it and returns a chunk data object
    :param cloud_chunk: the CloudChunk object
    :param symmetric_key: the 32 byte key for decryption
    :param is_compressed: indicates if compression should be used
    :return: a ChunkData object (the entries) InvalidTag exception if tag not matches
    """
    # encode public part of the chunk for aes gcm verification
    pub_part = _encode_cloud_chunk_public_part(cloud_chunk.key, cloud_chunk.key_version, cloud_chunk.policy_tag)

    # decrypt with aes gcm
    data = decrypt_aes_gcm_data(symmetric_key, cloud_chunk.mac_tag, pub_part, cloud_chunk.encrypted_data)

    # decompress data
    if is_compressed:
        data = decompress_data(data)
    # decode data
    return ChunkData.decode(data)
