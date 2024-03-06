#!/bin/bash

./compile.sh
pyinstaller --onefile --add-binary='./nia_start:.' --paths=./ui --name nia_start ui/main.py
pyinstaller nia_start.spec
