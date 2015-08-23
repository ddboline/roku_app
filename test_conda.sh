#!/bin/bash

nosetests roku_app/*.py
python3 ./roku_app/get_dev.py pvrusb2
