import ConfigParser
import argparse
import base64
import logging

import picamera
import time

import requests

from talosstorage.checks import BitcoinVersionedPrivateKey, get_priv_key
from talosstorage.chunkdata import ChunkData, TYPE_PICTURE_ENTRY, PictureEntry, create_cloud_chunk, \
    DataStreamIdentifier, compress_data
from timeit import default_timer as timer

from talosstorage.timebench import TimeKeeper


def capture_pi_image(filename):
    with picamera.PiCamera() as camera:
        camera.capture(filename)


def dummy_capture(filename):
    with open("../pylepton/haas.jpg", 'r') as f:
        picture = f.read()
    with open(filename, 'w') as f:
        return f.write(picture)


PRIVATE_KEY = BitcoinVersionedPrivateKey("cN5YgNRq8rbcJwngdp3fRzv833E7Z74TsF8nB6GhzRg8Gd9aGWH1")
NONCE = base64.b64decode("OU2HliHRUUZJokNvn84a+A==")
STREAMID = 1
TXID = "8cf71b7ed09acf896b40fc087e56d3d4dbd8cc346a869bb8a81624153c0c2b8c"
IP = "127.0.0.1"
# IP = "46.101.113.112"
# IP = "138.68.191.35"
PORT = 14000


def store_chunk(chunk, ip, port):
    req = requests.post("http://%s:%d/store_chunk" % (ip, port), data=chunk.encode())
    return req.reason, req.status_code


class ImageProducer(object):
    def __init__(self, name, start_block, bc_privatekey,
                 policy_nonce, stream_id, txid, ip='127.0.0.1', port=14000):
        self.name = name
        self.start_block = start_block
        self.bc_privatekey = BitcoinVersionedPrivateKey(bc_privatekey)
        self.policy_nonce = base64.b64decode(policy_nonce)
        self.stream_id = stream_id
        self.txid = txid
        self.ip = ip
        self.port = port
        self.local_private_key = get_priv_key(self.bc_privatekey)
        logging.basicConfig(filename='example.log', level=logging.DEBUG)

    def _generate_cloud_chunk(self, block_id, sym_key, chunk, timer_chunk):
        stream_ident = DataStreamIdentifier(self.bc_privatekey.public_key().address(),
                                            self.stream_id, self.policy_nonce, self.txid)

        return create_cloud_chunk(stream_ident, block_id, self.local_private_key, 0, sym_key, chunk,
                                  time_keeper=timer_chunk)

    def _store_to_cloud(self, chunk):
        req = requests.post("http://%s:%d/store_chunk" % (self.ip, self.port), data=chunk.encode())
        return req.reason, req.status_code

    def run_loop(self, image_capture, time_file, sym_key="a" * 16, interval=3600):
        cur_block = self.start_block
        while True:
            try:
                timer_chunk = TimeKeeper()
                # Take a picture
                picture_name = "%s%d.jpg" % (self.name, cur_block)
                image_capture(picture_name)

                # load image
                with open(picture_name, 'r') as f:
                    picture = f.read()

                chunk = ChunkData(type=TYPE_PICTURE_ENTRY)
                chunk.add_entry(PictureEntry(int(time.time()), picture_name, picture, time_keeper=timer_chunk))

                cur_time = timer()
                cloud_chunk = self._generate_cloud_chunk(cur_block, sym_key, chunk, timer_chunk)
                chunk_creation = timer() - cur_time

                len_normal = len(chunk.encode())
                len_compressed = len(compress_data(chunk.encode()))

                cur_time = timer()
                self._store_to_cloud(cloud_chunk)
                chunk_store = timer() - cur_time

                times = timer_chunk.logged_times

                time_file.write("%s, %s, %s, %s, %s, %.4f\n" % (times['chunk_compression'],
                                                                times['gcm_encryption'],
                                                                times['ecdsa_signature'],
                                                                chunk_creation,
                                                                chunk_store,
                                                                len_normal / len_compressed))
                cur_block += 1
                time_file.flush()
                time.sleep(interval)
            except RuntimeError as e:
                print e.message
                logging.error("Exception in round %d" % cur_block)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Run raspberrypi producer server client")
    parser.add_argument('--dhtport', type=int, help='dhtport', default=14000, required=False)
    parser.add_argument('--start_block', type=int, help='start_block', default=0, required=False)
    parser.add_argument('--dhtserver', type=str, help='dhtserver', default="46.101.113.112", required=False)
    parser.add_argument('--configfile', type=str, help='configfile', default='./config', required=False)
    parser.add_argument('--timefile', type=str, help='timefile', default='./time.log', required=False)
    parser.add_argument('--interval', type=int, help='start_block', default=3600, required=False)
    args = parser.parse_args()

    logging.basicConfig(filename='raspberry_time.log', level=logging.INFO)

    config = ConfigParser.RawConfigParser(allow_no_value=False)
    config.read(args.configfile)
    private_key = config.get("raspberry", "PRIVATE_KEY")
    policy_nonce = config.get("raspberry", "NONCE")
    stream_id = config.get("raspberry", "STREAMID")
    txid = config.get("raspberry", "TXID")

    producer = ImageProducer('raspberry', args.start_block, private_key, policy_nonce,
                             stream_id, txid, ip=args.dhtserver, port=args.dhtport)
    with open(args.timefile, 'w') as time_file:
        time_file.write("%s, %s, %s, %s, %s, %s\n" % ('chunk_compression',
                                                      'gcm_encryption',
                                                      'ecdsa_signature',
                                                      'total_creation',
                                                      'dht_store',
                                                      'compression_ratio'))
        producer.run_loop(capture_pi_image, time_file, interval=args.interval)
