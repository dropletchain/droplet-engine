import subprocess

"""
assumes lepton is installed:
https://github.com/dropbox/lepton

Provides simple api for lepton, ! no configuration options
"""


CMD = ["lepton", '-']

def compress_jpg_file(jpg_file):
    with open(jpg_file, 'r') as f:
        p = subprocess.Popen(CMD, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=f)
        out, _ = p.communicate()
    return out


def compress_jpg_data(data):
    p = subprocess.Popen(CMD, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    out, _ = p.communicate(input=data)
    return out


def decompress_jpg_file(lepton_file):
    return compress_jpg_file(lepton_file)


def decompress_jpg_data(data):
    return compress_jpg_data(data)

