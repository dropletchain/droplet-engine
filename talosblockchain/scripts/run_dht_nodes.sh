#!/bin/bash

if [ $# -lt 3 ]; then
    echo "usage ./cmd.sh <pulbic ip> <num_extra_nodes> <use_secure_dht_0_or_1> [<bootstrap node>]"
    exit 1
fi

if hash python2.7 2>/dev/null; then
    PYTHON_CMD=python2.7
else
    PYTHON_CMD=python
fi
echo $PYTHON_CMD

NUM_EXTRA_NODES=$2
CUR_PORT=14002
MAIN_SERVER_PORT=14001
KSIZE=10

ROOTPATH="./dhtstorage"
DB_PATH="$ROOTPATH/dhtdbs"
STATE_PATH="$ROOTPATH/dhtstates"
LOG_PATH="$ROOTPATH/logs"

PUBLIC_IP=$1
BOOTSTRAP_NODES="$4"

DHT_SECURE=$3

PROCESS_ID=""

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
STATE_PATH_FILE=$STATE_PATH/mainstate.state
cmd="$PYTHON_CMD dhtserver.py --restserver $PUBLIC_IP --dhtserver $PUBLIC_IP --ksize $KSIZE --dhtport $MAIN_SERVER_PORT --dhtdbpath $DB_PATH/mainnode --store_state_file $STATE_PATH_FILE --logfile $LOG_PATH/mainlog.log"

if [ -d "$STATE_PATH_FILE" ]; then
    cmd="$cmd --dht_cache_file $STATE_PATH_FILE"
fi

if [ $DHT_SECURE -eq 1 ]; then
    echo "secure dht"
    cmd="$cmd --secure"
fi

if [[  -z  $BOOTSTRAP_NODES ]]; then
    $cmd &
    PROCESS_ID="$PROCESS_ID $!"
else
    echo "Bootstrap nodes $BOOTSTRAP_NODES"
    cmd="$cmd --bootstrap $BOOTSTRAP_NODES"
    $cmd &
    PROCESS_ID="$PROCESS_ID $!"
fi
sleep 5

for ((c=1; c<=NUM_EXTRA_NODES; c++))
do
    STATE_PATH_FILE=$STATE_PATH/nodestate$c.state
    cmd="$PYTHON_CMD dhtserveronly.py --dhtserver $PUBLIC_IP --ksize $KSIZE --bootstrap $PUBLIC_IP:$MAIN_SERVER_PORT --dhtdbpath $DB_PATH/node$c --store_state_file $STATE_PATH_FILE --dhtport $CUR_PORT --logfile $LOG_PATH/node$c.log"
    if [ -d "$STATE_PATH_FILE" ]; then
        cmd="$cmd --dht_cache_file $STATE_PATH_FILE"
    fi

    if [ $DHT_SECURE -eq 1 ]; then
        echo "secure dht"
        cmd="$cmd --secure"
    fi
    echo "Start extra node $c"
    $cmd &
    PROCESS_ID="$PROCESS_ID $!"
	CUR_PORT=$((CUR_PORT + 1))
done

echo $PROCESS_ID > $ROOTPATH/processes.pid

cd $CUR_PATH