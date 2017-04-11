LOCAL_PATH=$(cd -P -- "$(dirname -- "$0")" && pwd -P)
CUR_PATH=$(pwd)

cd $LOCAL_PATH
cd ..

ROOTPATH="./dhtstorage"
PID_FILE=$ROOTPATH/processes.pid

PID=$(<$PID_FILE)

for dhtnode in $PID
do
    sudo kill $dhtnode
done

rm $PID_FILE

cd $CUR_PATH