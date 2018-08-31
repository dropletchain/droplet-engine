Our reference implementation of Droplet (https://arxiv.org/abs/1806.02057) is composed of three entities implemented in Python: 
 - the client engine
 - the storage-node engine
 - and the virtualchain.
 
Droplet's client engine is in charge of composing a data stream and data serialization, i.e., chunking, compression, and encryption. 
It handles viewing, setting, and modifying access permissions via the virtualchain.
It provides the interface to interact with the storage layer.
We utilize Pythons's cryptography library for our crypto functions;
AES encryption, SHA hashing, and ECDSA signature operations.
For compression, we use Lepton (from Dropbox) for images and zlib for all other value types.


The storage engine can either run on the cloud or nodes of a p2p storage network.
Currently, we have integrated drivers for Amazon's S3 storage service.
On individual nodes, we employ LevelDB, an efficient key-value database (LevelDB)
We have as well a realization of Droplet with a serverless computing platform 
with ASW Lambda serving as the interface to the storage (i.e., S3).
Once Lambda is invoked, it performs a lookup in the access control state machine to process the authorization request.
For comparison, we implement as well an OAuth2 authorization, based on AWS Cognito.
For the distributed storage, we build a DHT-based storage network.
We instantiate a Kademlia library and
extend it with the security features of S/Kademlia (i.e., public-private key pair per node, secure communication, signing of messages, hash of public key as node identifier, solving of a crypto puzzle to join the network).
The Kademlia protocol runs an asynchronous JSON/RPC over UDP
and the implementation relies on the Twisted framework to provide asynchronous communication. 
We add support for TCP connections for storing/fetching large chunks.
Our extensions amount to 2400~sloc.
We developed an Android client engine app on top of Droplet for our experiments with the Fitbit dataset

The virtualchain is instantiated from Blockstack and extended to implement our access control state 
machine.
The virtualchain scans the blockchain, filters relevant transactions, validates the encoded operations, and applies the outcome to the global state.
The state is persisted in an SQLite database.
The global state can either be queried through a REST API or accessed directly through the SQLite database.
Our extensions to the virtualchain amount to 1400 sloc.
As the underlying blockchain, we employ a Bitcoin test-network with a low block generation time to emulate a hybrid consensus blockchain (i.e., ca. 15~s block confirmation).


