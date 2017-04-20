import os
import sys

if len(sys.argv) < 3:
    print "Wrong input: <port_start> <port_connect(opt)> <path>"
    exit(-1)

start_port = int(sys.argv[1])
if len(sys.argv) == 4:
    path = sys.argv[3]
else:
    path = sys.argv[2]

with open(os.path.join(path, "bitcoin.conf"), 'w') as f:
    f.write("%s\n%s\n%s\n\n" % ("regtest=1", "dnsseed=0", "upnp=0"))
    f.write("port=%d\n" % (start_port,))
    f.write("rpcport=%d\n\n" % (start_port + 1,))
    if len(sys.argv) == 4:
        f.write("connect=127.0.0.1:%d\n" % (int(sys.argv[2]),))
    f.write("%s\n%s\n" % ("server=1", "rpcallowip=0.0.0.0/0"))
    f.write("rpcuser=admin%d\n" % (start_port,))
    f.write("rpcpassword=%d\n" % (start_port,))
