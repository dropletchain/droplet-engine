#!/bin/bash

if [ $# -lt 1 ]: then
    echo "usage ./cmd.sh <pulbic ip> [<bootstrap node>]"
    exit 1
fi

PYTHON_CMD=python
NUM_EXTRA_NODES=3
CUR_PORT=14002
MAIN_SERVER_PORT=14001

ROOTPATH="./dhtstorage"
DB_PATH="$ROOTPATH/dhtdbs"
STATE_PATH="$ROOTPATH/dhtstates"
LOG_PATH="$ROOTPATH/logs"

PUBLIC_IP=$1
BOOTSTRAP_NODES="$2"

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
cmd=$PYTHON_CMD dhtserver.py --restserver $PUBLIC_IP --dhtserver $PUBLIC_IP --dhtport $MAIN_SERVER_PORT --dhtdbpath $DB_PATH/mainnode --store_state_file $STATE_PATH/mainstate.state --logfile $LOG_PATH/mainlog.log
if [[  -z  $BOOTSTRAP_NODES ]]; then
    $cmd &
else
    $cmd --bootstrap $BOOTSTRAP_NODES &
fi
sleep 5

for ((c=1; c<=NUM_EXTRA_NODES; c++))
do
    echo "Start extra node $c"
    $PYTHON_CMD dhtserveronly.py --dhtserver $PUBLIC_IP --bootstrap $PUBLIC_IP:$MAIN_SERVER_PORT --dhtdbpath $DB_PATH/node$c --store_state_file $STATE_PATH/nodestate$c.state --dhtport $CUR_PORT --logfile $LOG_PATH/node$c.log &
	CUR_PORT=$((CUR_PORT + 1))
	sleep 5
done

cd $CUR_PATH