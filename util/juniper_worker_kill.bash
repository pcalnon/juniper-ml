#!/usr/bin/env bash


CNT=0; for i in $(ps aux | grep juniper | grep -v grep | grep pcalnon | awk -F " " '{print $2;}'); do CNT=$(( CNT + 1 )); echo "${CNT}. ${i}"; kill -KILL ${i}; done
