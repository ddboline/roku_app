#!/bin/bash

nosetests roku_app/*.py
./roku_app/get_dev.py pvrusb2
