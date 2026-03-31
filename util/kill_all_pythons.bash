#!/usr/bin/env bash


for i in $(ps aux | grep python | awk -F " " '{print $2;}'); do echo "${i}"; sudo kill -9 "${i}"; done
