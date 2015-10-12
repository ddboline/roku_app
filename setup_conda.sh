#!/bin/bash

sudo /opt/conda/bin/conda install -c https://conda.anaconda.org/ddboline --yes \
    numpy scipy dateutil requests matplotlib nose coverage

sudo apt-get install -y mplayer mpv mencoder numpy scipydateutil requests matplotlib nose coverage

mkdir -p ${HOME}/netflix/jobs ${HOME}/netflix/avi ${HOME}/netflix/log ${HOME}/netflix/mpg ${HOME}/netflix/tmp
