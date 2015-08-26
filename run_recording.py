#!/usr/bin/python
'''
    Script to record from roku device via WinTV HVR-1950
'''
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from sys import argv
from roku_app.record_roku import record_roku

if __name__ == '__main__':
    RECORDING_NAME = 'test_roku'
    RECORDING_TIME = 3600
    DO_FIX_PVR = False

    if len(argv) > 1:
        RECORDING_NAME = argv[1]
    if len(argv) > 2:
        try:
            RECORDING_TIME = int(argv[2])*60
        except ValueError:
            pass
    if len(argv) > 3:
        if argv[3] == 'fix_pvr':
            DO_FIX_PVR = True

    record_roku(RECORDING_NAME, RECORDING_TIME, DO_FIX_PVR)
