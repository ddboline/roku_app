#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import time
import requests

try:
    from util import run_command, send_command
except ImportError:
    from scripts.util import run_command, send_command

HOMEDIR = os.getenv('HOME')

def send_single_keypress(keypress):
    ''' wrapper around curl '''
    ROKU_IP = '192.168.0.101'
    if keypress == 'Wait':
        time.sleep(5)
    elif keypress == 'Gtalk':
        run_command('%s/bin/send_to_gtalk checkRoku' % HOMEDIR)
    else:
        result = requests.post('http://%s:8060/keypress/%s' % (ROKU_IP, keypress))
        if result.status_code != 200:
            return 'Error %d on keypress %s' % (result.status_code, keypress)
        print(result.status_code)
        print(result.text)
    return keypress

def send_to_roku(arglist=None):
    ''' main function, thumb and test run send message to record_roku, q quits, everything else sends to roku device '''

    retval = ''

    command_shortcuts = {'h': 'Home',
                      'l': 'Left',
                      'r': 'Right',
                      's': 'Select',
                      'f': 'Fwd',
                      'b': 'Back',
                      'u': 'Up',
                      'd': 'Down',
                      'p': 'Play',
                      'w': 'Wait',
                      'g': 'Gtalk',
                      'rv': 'Rev',
                      'ir': 'InstantReplay',
                      'if': 'Info',
                      'bs': 'Backspace',
                      'sc': 'Search',
                      'en': 'Enter',
                      'as': 'Lit_*',}

    if not arglist or len(arglist) == 0:
        return retval

    for arg in arglist:
        if arg in ['thumb', 'test', 'q']:
            retval = '%s%s' % (retval, send_command(arg, portno=10888))
        elif arg == 'run':
            time.sleep(5)
            print('run\n')
            run_command('sh %s/netflix/test.sh' % HOMEDIR)
            retval = '%srun' % retval
        elif arg in command_shortcuts:
            retval = send_single_keypress(command_shortcuts[arg])
            retval = '%s%s' % (retval, 'command %s' % arg)
        else:
            retval = send_single_keypress(arg)
    return retval

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
