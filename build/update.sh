#!/bin/bash
if [[ $1 = 'u' || $1 = 'update' ]]; then

cp ../src/map.py main.py
cp ../src/Warnings.py .
[[ -d img/ ]] || mkdir img/
cp -r ../src/img/png/ img/

elif [[ $1 = 'b' || $1 = 'build' ]]; then

./update.sh && buildozer -v android debug

elif [[ $1 = 'i' || $1 = 'install' ]]; then

adb install -r `ls -1 | tail -n1`

elif [[ $1 = 'l' || $1 = 'logcat' ]]; then

adb logcat | grep python

elif [[ -z $1 || $1 = '-h' || $1 = 'help' ]]; then

printf "usage: update.sh [update|build|install|logcat]\n"

fi
