#!/bin/bash

nosetests --with-coverage --cover-package=roku_app roku_app/*.py
python3 ./roku_app/get_dev.py pvrusb2
