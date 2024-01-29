#!/bin/bash

xhost +
docker build -t startim .
echo -e "To start app type: \e[1;34mpython3 ui/main.py\e[0m"
docker run -it -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix startim
export QT_DEBUG_PLUGINS=1
