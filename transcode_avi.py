#!/usr/bin/python
'''
    Script to record from roku device via WinTV HVR-1950
'''
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
from roku_app.remcom import make_transcode_script

if __name__ == '__main__':
    if len(os.sys.argv) > 1:
        MOVIE_FILENAME = os.sys.argv[1]
    else:
        print('python transcode_avi.py <file>')
        exit(0)

    make_transcode_script(MOVIE_FILENAME)
