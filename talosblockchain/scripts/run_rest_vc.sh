#!/bin/bash

LOCAL_PATH=$(cd -P -- "$(dirname -- "$0")" && pwd -P)
CUR_PATH=$(pwd)

cd $LOCAL_PATH
cd ..

FOLDER="./vcfiles"

if [ ! -d "FOLDER" ]; then
    echo "create folders"
    mkdir $FOLDER
fi

if hash python2.7 2>/dev/null; then
    cmd=python2.7
else
    cmd=python
fi

export BLOCKSTACK_TESTNET=1
export VIRTUALCHAIN_WORKING_DIR=$LOCAL_PATH/../$FOLDER
export BLOCKSTACK_DEBUG=1

$cmd restvcapi.py $* 2>&1 | tee $LOCAL_PATH/../$FOLDER/vc.log &

cd $CUR_PATH
