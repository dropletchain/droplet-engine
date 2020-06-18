#© 2017-2020, ETH Zurich, D-INFK, lubu@inf.ethz.ch

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

from talosstorage.chunkdata import hash_sign_data

data = "Hello"
private_key = ec.generate_private_key(ec.SECP256K1, default_backend())

for i in range(100):
    data += str(i)
    sig = hash_sign_data(private_key, data)
    r, s = decode_dss_signature(sig)
    print "Len: %d R: %s S: %s" % (len(sig), str(r), str(s))