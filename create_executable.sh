#!/bin/bash

current_date=$(date +"%d.%m.%Y")
output_name="nia_start_$current_date"

./compile.sh -j 4
pyinstaller --onefile --add-binary='./nia_start:.' --add-data='./icons:icons' --paths=./ui --name "$output_name" ui/main.py
pyinstaller nia_start.spec

cp -rv icons/ dist/icons
cp -v nia_start dist/nia_start