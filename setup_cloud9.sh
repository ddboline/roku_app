#!/bin/bash

sudo apt-get update
sudo apt-get install -y python-numpy python-scipy python-dateutil python-requests python-matplotlib python-pytest\
                        mplayer mpv mencoder python-coverage python-setuptools python-dev

mkdir -p ${HOME}/netflix/jobs ${HOME}/netflix/avi ${HOME}/netflix/log ${HOME}/netflix/mpg ${HOME}/netflix/tmp
