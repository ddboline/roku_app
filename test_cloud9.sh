#!/bin/bash

py.test --cov=roku_app roku_app/*.py

# pyreverse roku_app
# for N in classes packages; do dot -Tps ${N}*.dot > ${N}.ps ; done

./roku_app/get_dev.py pvrusb2
