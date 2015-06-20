# -*- coding: utf-8 -*-
"""
Created on Fri Jun 19 17:08:47 2015

@author: ddboline
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
from get_dev import get_dev
from util import run_command

def list_running_recordings(devname='/dev/video0'):
    ''' list any currently running recordings '''
    pids = []
    _cmd = 'fuser -a %s 2> /dev/null' % devname
    for line in run_command(_cmd, do_popen=True):
        try:
            pids.append(int(line.strip()))
        except ValueError:
            pass
    for line in run_command('ps -eF 2> /dev/null', do_popen=True):
        ents = line.strip().split()
        try:
            pid = int(ents[1])
            ppid = int(ents[2])
            if pid in pids or ppid in pids:
                if pid not in pids:
                    pids.append(pid)
                if ppid not in pids:
                    pids.append(ppid)
        except ValueError:
            continue
    return pids

def record_roku(recording_name='test_roku', recording_time=3600,
                do_fix_pvr=False):
    '''
        main function, record video from roku device via wintv encoder
        options:
            name, duration, fix_pvr (optional),
    '''

    device = get_dev('pvrusb')
    
