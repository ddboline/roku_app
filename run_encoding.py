#!/usr/bin/python
'''
    Script to record from roku device via WinTV HVR-1950
'''
from __future__ import (absolute_import, division, print_function, unicode_literals)

from time import sleep

from roku_app.run_encoding import run_encoding

if __name__ == '__main__':
    try:
        run_encoding()
    except Exception as exc:
        print('Caught exception %s' % exc)
        sleep(10)
