#!/bin/bash

./compile.sh
pyinstaller --onefile --add-binary='./argos_nia_start:.' --paths=./ui ui/main.py

