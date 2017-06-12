import ConfigParser
import argparse
import base64
import logging
import os

import picamera
import time

import requests
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
from talosstorage.checks import BitcoinVersionedPrivateKey, get_priv_key
from talosstorage.chunkdata import ChunkData, TYPE_PICTURE_ENTRY, PictureEntry, create_cloud_chunk, \
    DataStreamIdentifier, compress_data
from timeit import default_timer as timer

from talosstorage.timebench import TimeKeeper


def capture_pi_image(filename):
    with picamera.PiCamera() as camera:
        #camera.hflip = True
        #camera.vflip = True
        time.sleep(1)
        camera.capture(filename)


def dummy_capture(filename):
    with open("../pylepton/haas.jpg", 'r') as f:
        picture = f.read()
    with open(filename, 'w') as f:
        return f.write(picture)


class ImageProducer(object):
    def __init__(self, name, start_time, bc_privatekey,
                 policy_nonce, stream_id, txid, ip='127.0.0.1', port=14000):
        self.name = name
        self.start_time = start_time
        self.bc_privatekey = BitcoinVersionedPrivateKey(bc_privatekey)
        self.policy_nonce = base64.b64decode(policy_nonce)
        self.stream_id = stream_id
        self.txid = txid
        self.ip = ip
        self.port = port
        self.local_private_key = get_priv_key(self.bc_privatekey)

    def _generate_cloud_chunk(self, block_id, sym_key, chunk, timer_chunk):
        stream_ident = DataStreamIdentifier(self.bc_privatekey.public_key().address(),
                                            self.stream_id, self.policy_nonce, self.txid)

        return create_cloud_chunk(stream_ident, block_id, self.local_private_key, 0, sym_key, chunk,
                                  time_keeper=timer_chunk)

    def _store_to_cloud(self, chunk_encoded):
        req = requests.post("http://%s:%d/store_chunk" % (self.ip, self.port), data=chunk_encoded)
        return req.reason, req.status_code

    def run_loop(self, image_capture, time_file, sym_key="a" * 16, interval=3600):
        while True:
            try:
                timer_chunk = TimeKeeper()
                total_id = timer_chunk.start_clock_unique()
                timestamp_data = int(time.time())
                block_id = (timestamp_data - self.start_time) / interval
                # Take a picture
                picture_name = "%s%d.jpg" % (self.name, block_id)
                image_capture(picture_name)
                print picture_name

                # load image
                with open(picture_name, 'r') as f:
                    picture = f.read()

                chunk_tmp = ChunkData()

                chunk_tmp.add_entry(PictureEntry(timestamp_data, picture_name, picture, time_keeper=timer_chunk))

                cur_time = timer()
                cloud_chunk = self._generate_cloud_chunk(block_id, sym_key, chunk_tmp, timer_chunk)
                chunk_creation = timer() - cur_time

                len_normal = len(chunk_tmp.encode(use_compression=False))
                len_compressed = len(compress_data(chunk_tmp.encode(use_compression=True)))

                cloud_chunk_encoded = cloud_chunk.encode()
                length_final = len(cloud_chunk_encoded)
                cur_time = timer()
                self._store_to_cloud(cloud_chunk_encoded)
                chunk_store = timer() - cur_time

                times = timer_chunk.logged_times

                time_file.write("%s, %s, %s, %s, %s, %s, %d, %d, %d,\n" % (times['chunk_compression'],
                                                                           times['gcm_encryption'],
                                                                           times['ecdsa_signature'],
                                                                           times['time_lepton_compression'],
                                                                           chunk_creation * 1000,
                                                                           chunk_store * 1000,
                                                                           len_normal,
                                                                           len_compressed,
                                                                           length_final))
                time_file.flush()
                timer_chunk.stop_clock_unique('time_total', total_id)
                time.sleep(interval - int(timer_chunk.logged_times['time_total'] / 1000))
            except RuntimeError as e:
                print e.message
                logging.error("Exception occured %s" % e.message)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Run raspberrypi producer server client")
    parser.add_argument('--dhtport', type=int, help='dhtport', default=14000, required=False)
    parser.add_argument('--start_block', type=int, help='start_block', default=1497225600, required=False)
    parser.add_argument('--dhtserver', type=str, help='dhtserver', default="46.101.113.112", required=False)
    parser.add_argument('--configfile', type=str, help='configfile', default='./config', required=False)
    parser.add_argument('--timefile', type=str, help='timefile', default='./time.log', required=False)
    parser.add_argument('--interval', type=int, help='interval', default=7200, required=False)
    parser.add_argument('--name', type=str, help='name', default="./photos/rapsberry", required=False)
    args = parser.parse_args()

    config = ConfigParser.RawConfigParser(allow_no_value=False)
    config.read(args.configfile)
    private_key = config.get("raspberry", "PRIVATE_KEY")
    policy_nonce = config.get("raspberry", "NONCE")
    stream_id = config.get("raspberry", "STREAMID")
    txid = config.get("raspberry", "TXID")

    producer = ImageProducer(args.name, args.start_block, private_key, policy_nonce,
                             stream_id, txid, ip=args.dhtserver, port=args.dhtport)
    with open(args.timefile, 'w') as time_file:
        time_file.write("%s, %s, %s, %s, %s, %s, %s ,%s, %s\n" % ('chunk_compression',
                                                                  'gcm_encryption',
                                                                  'ecdsa_signature',
                                                                  'lepton_compression',
                                                                  'total_creation',
                                                                  'dht_store',
                                                                  'length normal',
                                                                  'length compressed',
                                                                  'final_length'))
        producer.run_loop(capture_pi_image, time_file, interval=args.interval)
