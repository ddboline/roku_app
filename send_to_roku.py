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

    if HOSTNAME != 'dilepton-tower':
        CMD = 'python %s/scripts/send_to_roku.py' % HOMEDIR
        for arg in os.sys.argv[1:]:
            CMD = '%s %s' % (CMD, arg)
        run_command('ssh ddboline@%s \"%s\"' % (REMOTEHOST, CMD))
    else:
        RETVAL = send_to_roku(os.sys.argv[1:])
        if len(RETVAL) > 0 and 'command' not in RETVAL:
            print(RETVAL.strip())
