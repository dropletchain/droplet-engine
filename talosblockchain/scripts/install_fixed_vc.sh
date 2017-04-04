#!/bin/bash

LOCAL_PATH=$(cd -P -- "$(dirname -- "$0")" && pwd -P)
CUR_PATH=$(pwd)

sudo apt-get install python-pip libffi-dev python-dev build-essential libssl-dev libffi-dev


cd $LOCAL_PATH
cd ..
cd protocoin
sudo python setup.py install
cd ..
cd virtualchain
sudo python setup.py install
cd ..


pip install flask
pip install kademlia
pip install requests
pip install cryptography
pip install cachetools
pip install leveldb
pip install --upgrade pyopenssl
pip install service_identity

cd $CUR_PATH
