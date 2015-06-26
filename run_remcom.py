#!/usr/bin/python
'''
    Script to record from roku device via WinTV HVR-1950
'''
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
from roku_app.remcom_test import remcom_test_main

if __name__ == '__main__':
    if len(os.sys.argv) > 4:
        MOVIE_FILENAME = os.sys.argv[1]
        OUTPUT_DIR = os.sys.argv[2]
        BEGIN_TIME = int(os.sys.argv[3])
        END_TIME = int(os.sys.argv[4])
    else:
        print('python remcom_test.py <file> <dir> <begin> <end>')
        exit(0)

    remcom_test_main(MOVIE_FILENAME, OUTPUT_DIR, BEGIN_TIME, END_TIME)
