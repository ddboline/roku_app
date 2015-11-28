#!/bin/bash

nosetests --with-coverage --cover-package=roku_app roku_app/*.py

# pyreverse roku_app
# for N in classes packages; do dot -Tps ${N}*.dot > ${N}.ps ; done

python3 ./roku_app/get_dev.py pvrusb2
