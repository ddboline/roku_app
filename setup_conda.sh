#!/bin/bash

sudo /opt/conda/bin/conda install -c https://conda.anaconda.org/ddboline --yes numpy scipy dateutil requests matplotlib nose

sudo apt-get install -y mplayer mpv mencoder

mkdir -p ${HOME}/netflix/jobs ${HOME}/netflix/avi ${HOME}/netflix/log ${HOME}/netflix/mpg ${HOME}/netflix/tmp
