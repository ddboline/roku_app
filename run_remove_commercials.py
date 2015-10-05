#!/usr/bin/python
'''
    Script to record from roku device via WinTV HVR-1950
'''
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
from roku_app.remove_commercials import remove_commercials

if __name__ == '__main__':
    INFILE = os.sys.argv[1]
    OUTFILE = INFILE.split('/')[-1]
    if len(os.sys.argv) > 2:
        OUTFILE = os.sys.argv[2]
    if len(os.sys.argv) > 3:
        TIMING_FILENAME = os.sys.argv[3]
    TIMING_STRING = open(TIMING_FILENAME, 'r').read()

    remove_commercials(INFILE, OUTFILE, TIMING_STRING)
