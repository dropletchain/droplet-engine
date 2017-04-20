#!/bin/bash

LOCAL_PATH=$(cd -P -- "$(dirname -- "$0")" && pwd -P)
CUR_PATH=$(pwd)

if [ "$(uname)" == "Darwin" ]; then

else
    sudo apt-get install python-pip libffi-dev python-dev build-essential libssl-dev libffi-dev
fi


cd $LOCAL_PATH
cd ..

echo "Install lepton"
git clone https://github.com/dropbox/lepton.git
sudo apt-get install -y autogen autoconf
cd lepton
./autogen.sh
./configure
make -j8
make check -j8
sudo make install
cd ..

cd protocoin
sudo python setup.py install
cd ..
cd virtualchain
sudo python setup.py install
cd ..

sudo pip install pillow
sudo pip install flask
sudo pip install kademlia
sudo pip install requests
sudo pip install cryptography
sudo pip install cachetools
sudo pip install leveldb
sudo pip install --upgrade pyopenssl
sudo pip install service_identity

cd $CUR_PATH
