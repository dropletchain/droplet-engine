#!/bin/bash

PYTHON_CMD=python
NUM_EXTRA_NODES=3
CUR_PORT=14002
MAIN_SERVER_PORT=14001

ROOTPATH="./dhtstorage"
DB_PATH="$ROOTPATH/dhtdbs"
STATE_PATH="$ROOTPATH/dhtstates"
LOG_PATH="$ROOTPATH/logs"

BOOTSTRAP_NODES=""

LOCAL_PATH=$(cd -P -- "$(dirname -- "$0")" && pwd -P)
CUR_PATH=$(pwd)


cd $LOCAL_PATH
cd ..

if [ ! -d "$ROOTPATH" ]; then
    echo "create folders"
    mkdir $ROOTPATH
    mkdir $DB_PATH
    mkdir $STATE_PATH
    mkdir $LOG_PATH
fi


echo "Start main node"
$PYTHON_CMD dhtserver.py --dhtport $MAIN_SERVER_PORT --dhtdbpath $DB_PATH/mainnode --store_state_file $STATE_PATH/mainstate.state --logfile $LOG_PATH/mainlog.log --vcport &

sleep 5

for ((c=1; c<=NUM_EXTRA_NODES; c++))
do
    echo "Start extra node $c"
    $PYTHON_CMD dhtserveronly.py --bootstrap 127.0.0.1:$MAIN_SERVER_PORT --dhtdbpath $DB_PATH/node$c --store_state_file $STATE_PATH/nodestate$c.state --dhtport $CUR_PORT --logfile $LOG_PATH/node$c.log &
	CUR_PORT=$((CUR_PORT + 1))
	sleep 5
done

cd $CUR_PATH