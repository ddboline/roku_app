# -*- coding: utf-8 -*-
"""
Created on Fri Jun 19 19:58:06 2015

@author: ddboline
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import time
import logging
from get_dev import get_dev
from multiprocessing import Process
from util import run_command, check_dmesg_for_ooops, run_fix_pvr

HOMEDIR = os.getenv('HOME')

class OoopsException(Exception):
    pass

class RunningException(Exception):
    pass

class RecordRoku(object):
    use_mplayer = True
    use_handbrake_for_test_script = False
    use_handbrake_for_transcode_script = False
    turn_on_commands = True
    testscript = '%s/netflix/test.sh' % HOMEDIR
    killscript = '%s/netflix/kill_job.sh' % HOMEDIR

    def __init__(self, recording_name='test_roku', recording_time=3600,
                 do_fix_pvr=False):
        self.list_of_subprocesses = []
        self.roku_socket_file = '/tmp/.record_roku_socket'
        self.recording_name = recording_name
        self.recording_time = recording_time
        self.device = get_dev('pvrusb')
        self.logfname = '%s/netflix/log/%s_0.out' % (HOMEDIR,
                                                     self.recording_name)
        logging.basicConfig(filename=self.logfname, level=logging.DEBUG)
        
    def start_recording(self):
        logging.info('recording %s for %d seconds\n' % (self.recording_name,
                                                        self.recording_time))

        ### This needs to run before the server_thread is started
        if self.recording_name != 'test_roku':
            self.kill_running_recordings()
            pids = self.list_running_recordings(self.device)
            self.kill_running_recordings(pids)
            logging.info('killing %s \n' % pids)
        else:
            pids = self.list_running_recordings(self.device)
            if len(pids) > 0:
                print('already recording %s\n' % pids)
                logging.info('already recording %s\n' % pids)
                raise RunningException

        
    def initialize_roku(self, do_fix_pvr=False, msg_q=None):
        ''' initialize wintv device '''
    
        if msg_q:
            msg_q.put('begin initialization')
    
        if check_dmesg_for_ooops():
            _msg = 'signature of pvrusb2 ooops detected before unloading module,' +\
                   'stopping execution immediately'
            run_command('send_to_gtalk \"%s\"' % _msg)
            self.kill_running_recordings(self.list_of_subprocesses)
            raise OoopsException
    
        fix_pvr_process = Process(target=run_fix_pvr,\
                                  args=(self.turn_on_commands, do_fix_pvr))
        fix_pvr_process.start()
        self.list_of_subprocesses.append(fix_pvr_process.pid)
    
        while fix_pvr_process.is_alive():
            if check_dmesg_for_ooops():
                _msg = 'signature of pvrusb2 ooops detected while unloading ' +\
                       'module, stopping execution immediately'
                run_command('send_to_gtalk \"%s\"' % _msg)
                self.kill_running_recordings(self.list_of_subprocesses)
                raise OoopsException
            time.sleep(5)
    
        self.list_of_subprocesses.remove(fix_pvr_process.pid)
        fix_pvr_process.join()
    
        if msg_q:
            msg_q.put('roku initialized')
        logging.info('roku initialized\n')

    def kill_running_recordings(self, pids=None):
        ''' kill list of pids '''
        if os.path.exists(self.killscript):
            run_command('sh %s' % self.killscript)
            os.remove(self.killscript)
        if os.path.exists(self.testscript):
            os.remove(self.testscript)
        if pids:
            _cmd = 'kill -9'
            for pid in pids:
                _cmd = '%s %d' % (_cmd, pid)
            run_command(_cmd)
