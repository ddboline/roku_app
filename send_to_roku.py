#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
    script to send commands to roku
'''

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

from roku_app.util import run_command
from roku_app.roku_utils import send_to_roku, HOMEDIR

if __name__ == '__main__':
    HOSTNAME = os.uname()[1]
    REMOTEHOST = 'ddbolineathome.mooo.com'
    USER = 'ddboline'

    if HOSTNAME != 'dilepton-tower':
        SCRIPT_DIR = '%s/setup_files/build/roku_app/' % HOMEDIR
        CMD = 'python %s/send_to_roku.py' % SCRIPT_DIR
        for arg in os.sys.argv[1:]:
            CMD = '%s %s' % (CMD, arg)
        run_command('ssh %s@%s \"%s\"' % (USER, REMOTEHOST, CMD))
    else:
        RETVAL = send_to_roku(os.sys.argv[1:])
        if len(RETVAL) > 0 and 'command' not in RETVAL:
            print(RETVAL.strip())
