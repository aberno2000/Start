#!/bin/bash

xhost +local:docker
docker build -t startim .
docker run -it -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix -v /dev/dri:/dev/dri startim /bin/bash -c "./nia_start"
