#!/bin/bash

sudo /opt/conda/bin/conda install -c https://conda.anaconda.org/ddboline --yes \
    numpy scipy python-dateutil requests matplotlib nose coverage

mkdir -p ${HOME}/netflix/jobs ${HOME}/netflix/avi ${HOME}/netflix/log ${HOME}/netflix/mpg ${HOME}/netflix/tmp
