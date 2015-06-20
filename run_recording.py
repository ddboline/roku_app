#!/usr/bin/python
'''
    Script to record from roku device via WinTV HVR-1950
'''
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
from roku_app.roku_utils import record_roku

#from roku_app import roku_app
#roku_app.run(debug=True)

if __name__ == '__main__':
    _recording_name = 'test_roku'
    _recording_time = 3600
    _do_fix_pvr = False

    if len(os.sys.argv) > 1:
        _recording_name = os.sys.argv[1]
    if len(os.sys.argv) > 2:
        try:
            _recording_time = int(os.sys.argv[2])*60
        except ValueError:
            pass
    if len(os.sys.argv) > 3:
        if os.sys.argv[3] == 'fix_pvr':
            _do_fix_pvr = True

    record_roku(recording_name=_recording_name,
                recording_time=_recording_time,
                do_fix_pvr=_do_fix_pvr)
