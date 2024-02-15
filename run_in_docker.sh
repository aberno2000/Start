#!/bin/bash

xhost +
docker build -t startim .
docker run -it -e DISPLAY=$DISPLAY -e QT_DEBUG_PLUGINS=1 -v /tmp/.X11-unix:/tmp/.X11-unix startim conda run -n startenv bash -c "./compile.sh -r && python ui/main.py"
