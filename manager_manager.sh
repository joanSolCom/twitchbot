#!/bin/bash

while true; do
    echo "I'm alive"
    python bot_manager.py &
    sleep 3h
    echo "I'm Awake"
    for pid in `ps -aux | grep "python bot_manager" | grep -v grep | awk '{print $2}'`;
    do
    	kill -15 $pid;
    done

done

