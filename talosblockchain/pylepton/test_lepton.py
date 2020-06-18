#© 2017-2020, ETH Zurich, D-INFK, lubu@inf.ethz.ch

import unittest

from pylepton.lepton import *


class TestLepton(unittest.TestCase):

    def test_compress_file(self):
        with open("./pylepton/haas.jpg", 'r') as f:
            pic = f.read()

        out = compress_jpg_file("./pylepton/haas.jpg")
        print "Len in: %d Len out: %d" % (len(pic), len(out))
        self.assertTrue(len(out) > 0)

    def test_compress_data(self):
        with open("./pylepton/haas.jpg", 'r') as f:
            pic = f.read()
        out = compress_jpg_data(pic)
        print "Len in: %d Len out: %d" % (len(pic), len(out))
        self.assertTrue(len(out) > 0)

    def test_decompress_data(self):
        with open("./pylepton/haas.jpg", 'r') as f:
            pic = f.read()
        out = compress_jpg_data(pic)
        print "Len in: %d Len out: %d" % (len(pic), len(out))
        self.assertTrue(len(out) > 0)
        after = compress_jpg_data(out)
        print "Len after: %d Len original: %d" % (len(after), len(pic))
        self.assertEquals(pic, after)


