#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

from roku_app.util import run_command
from roku_app.roku_utils import send_to_roku, HOMEDIR

if __name__ == '__main__':
    hostname = os.uname()[1]
    remotehost = 'ddbolineathome.mooo.com'

    if hostname != 'dilepton-tower':
        _cmd = 'python %s/scripts/send_to_roku.py' % HOMEDIR
        for arg in os.sys.argv[1:]:
            _cmd = '%s %s' % (_cmd, arg)
        run_command('ssh ddboline@%s \"%s\"' % (remotehost, _cmd))
    else:
        retval = send_to_roku(os.sys.argv[1:])
        if len(retval) > 0 and 'command' not in retval:
            print(retval.strip())
