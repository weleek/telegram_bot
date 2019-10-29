#!/usr/bin/env bash

SCRIPT_PATH=$( cd "$(dirname "$0")" ; pwd )

python -m grpc_tools.protoc -I $SCRIPT_PATH/proto network.proto --python_out=$SCRIPT_PATH --grpc_python_out=$SCRIPT_PATH