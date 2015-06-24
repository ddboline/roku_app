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
        movie_filename = os.sys.argv[1]
        output_dir = os.sys.argv[2]
        _begin_time = int(os.sys.argv[3])
        _end_time = int(os.sys.argv[4])
    else:
        print('python remcom_test.py <file> <dir> <begin> <end>')
        exit(0)

    remcom_test_main(movie_filename, output_dir, _begin_time, _end_time)
