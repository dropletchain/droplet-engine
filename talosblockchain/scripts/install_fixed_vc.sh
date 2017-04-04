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

sudo pip install flask
sudo pip install kademlia
sudo pip install requests
sudo pip install cryptography
sudo pip install cachetools

cd $CUR_PATH
