#!/bin/bash

./compile.sh
pyinstaller --onefile --add-binary='./argos_nia_start:.' --paths=./ui --name NIA_Start ui/main.py
pyinstaller NIA_Start.spec

