#!/bin/bash

py.test --cov=roku_app roku_app/*.py
python3 ./roku_app/get_dev.py pvrusb2
