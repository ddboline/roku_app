#!/bin/bash

### hack...
export LANG="C.UTF-8"

sudo bash -c "echo deb ssh://ddboline@ddbolineathome.mooo.com/var/www/html/deb/trusty/python3/devel ./ > /etc/apt/sources.list.d/py2deb2.list"
sudo apt-get update
sudo apt-get install -y python3-numpy=1.\* python3-scipy python3-dateutil python3-requests python3-matplotlib python3-nose\
                        mplayer mpv mencoder python3-coverage python3-setuptools python3-dev

mkdir -p ${HOME}/netflix/jobs ${HOME}/netflix/avi ${HOME}/netflix/log ${HOME}/netflix/mpg ${HOME}/netflix/tmp
