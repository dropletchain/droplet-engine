# Prototype implementation Talos Blockchain Storage System

## Description
The Talos blockchain storage system enables IoT devices to store straming data persistently, 
without worrying about trusting a powerful third-party storage provider. The data is stored in a 
decentralized system, which protects your data with encryption and access control. Furthermore, 
we allow sharing to third party services with policies to ensure that only the defined parties have access 
to the data. 

## Design
The system has several layers, a blockchain, a virtualchain, a routing layer and a storage layer. The blockchain allows 
the user create, modify its access policy by defining the operations in a blockchain transaction. 
In the second layer, the virtual chain processes these operations and creates a database of access policies per user. 
As the data is stored decentralised, we employ a distributed hash table (DHT) routing layer for storing and fetching 
the data from the specific nodes. Finally, the storage layer defines how the streaming data is partitioned, encrypted 
and linked to the policy and ensures that the policies are enforced.

## Implementation 
We partitioned the project in the following way:
| Layer | Location | Description |
| ------ | ----------- | ----------- |
| blockchain    |  Bitcoin blockcahin  | Traditional bitcoin node |
| virtualchain | talosvc | Implements the virtualchain and client code for creating policies  |
| routing | talosdht | Implements a S/Kademlia DHT  |
| storage | talosstorage | Implements stream to chunk part, compression, crypto and the checks |

## Run

The main scripts are located in the scripts folder:

| Script | Description |
| ------ | ----------- |
| install_dependencies.sh  | Install libraries and dependecies |
| run_bitcoin_test_node.sh | Runs a bitcoin testnode |
| run_rest_vc.sh    | Runs a virtualchain node with a rest api (assumes bitcoin node running)|
| run_policy_client.sh   | Runs a interactive policy client for creating policies (assumes bitcoin node running)|
| run_dht_nodes.sh   | Runs upto n DHT nodes (assumes bitcoin and virtualchain node running)|
| terminate_dht_nodes.sh   | Terminates the dht nodes|

Other folders:

| Folder | Description |
| ------ | ----------- |
| benchmark | Benchamrk python scripts |
| exp_virtualchain | Experimental code |
| global_tests   | Basic tests for testing the global API |
| run_policy_client.sh   | Runs a interactive policy client for creating policies (assumes bitcoin node running)|
| run_dht_nodes.sh   | Runs upto n DHT nodes (assumes bitcoin and virtualchain node running)|
| terminate_dht_nodes.sh   | Terminates the dht nodes|


## Used Libraries 

- virtualchain (Blockstack)
- kademlia (bmuller)
- LevelDB (Storage)
- cryptography (Python crypto library (OpenSSL))