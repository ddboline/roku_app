#!/usr/bin/python
'''
    Script to record from roku device via WinTV HVR-1950
'''
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
from roku_app.record_roku import record_roku

if __name__ == '__main__':
    RECORDING_NAME = 'test_roku'
    RECORDING_TIME = 3600
    DO_FIX_PVR = False

    if len(os.sys.argv) > 1:
        RECORDING_NAME = os.sys.argv[1]
    if len(os.sys.argv) > 2:
        try:
            RECORDING_TIME = int(os.sys.argv[2])*60
        except ValueError:
            pass
    if len(os.sys.argv) > 3:
        if os.sys.argv[3] == 'fix_pvr':
            DO_FIX_PVR = True

    record_roku(recording_name=RECORDING_NAME,
                             recording_time=RECORDING_TIME,
                             do_fix_pvr=DO_FIX_PVR)
