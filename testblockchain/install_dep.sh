#!/bin/bash

sudo apt-get update
sudo apt-get install --yes software-properties-common
sudo apt-get install python 
sudo add-apt-repository --yes ppa:bitcoin/bitcoin
sudo apt-get update
sudo apt-get install --yes bitcoind make