#!/bin/bash

kill -s 9 `ps -aux | grep ./main | awk '{print $2}'`