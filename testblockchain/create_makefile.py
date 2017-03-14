import sys, os

if len(sys.argv) < 2:
    print "Wrong input: <num_nodes>"
    exit(-1)

num_nodes = int(sys.argv[1])

intent="	"

with open("Makefile", 'w') as f:
    f.write("%s\n%s\n%s\n" % ("BITCOIND=bitcoind", "BITCOINCLI=bitcoin-cli", "BLOCKS=1"))
    for i in range(1, num_nodes+1):
         f.write("B%d=-datadir=node%d\n" % (i, i))
    f.write("\n")
    f.write("start:\n")
    for i in range(1, num_nodes+1):
        f.write("%s$(BITCOIND) $(B%d) -daemon\n" % (intent, i))

    f.write("\ngenerate:\n")
    f.write("%s$(BITCOINCLI) $(B1) generate $(BLOCKS)\n" % (intent,))

    f.write("\ngetinfo:\n")
    for i in range(1, num_nodes+1):
        f.write("%s$(BITCOINCLI) $(B%d) getinfo\n" % (intent, i))

    f.write("\nstop:\n")
    for i in range(1, num_nodes+1):
        f.write("%s$(BITCOINCLI) $(B%d) stop\n" % (intent, i))

    f.write("\nclean:\n")
    for i in range(1, num_nodes+1):
        f.write("%sfind node%d/regtest/* -not -name 'server.*' -delete\n" % (intent, i))

    f.write("\ndelete:\n")
    for i in range(1, num_nodes+1):
        f.write("%srm -r ./node%d" % (intent, i))