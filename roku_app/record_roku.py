#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
    Script to record from roku device via WinTV HVR-1950
'''
from __future__ import print_function

import os
import time
import get_dev
import subprocess
import multiprocessing
import socket
import lockfile

from .send_to_roku import send_to_roku
from .util import (run_command, get_length_of_mpg, make_thumbnails,
                   run_fix_pvr, check_dmesg_for_ooops,
                   make_audio_analysis_plots, make_time_series_plot,
                   OpenUnixSocketServer, OpenSocketConnection)

### Global variables, immutable
USE_MPLAYER = True
USE_HANDBAKE_FOR_TEST_SCRIPT = False
USE_HANDBAKE_FOR_TRANSCODE_SCRIPT = False
DEVICE = '/dev/video0'
TURN_ON_COMMANDS = True
HOMEDIR = os.getenv('HOME')

ROKU_SOCKET_FILE = '/tmp/.record_roku_socket'
MAINLOCK = '/tmp/.record_roku.lock'
TESTSCRIPT = '%s/netflix/test.sh' % HOMEDIR
KILLSCRIPT = '%s/netflix/kill_job.sh' % HOMEDIR

GLOBAL_LOCKFILES = {}
GLOBAL_LIST_OF_SUBPROCESSES = []
LOGFILE = None

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

def kill_running_recordings(pids=None):
    ''' kill list of pids '''
    if os.path.exists(KILLSCRIPT):
        run_command('sh %s' % KILLSCRIPT)
        os.remove(KILLSCRIPT)
    if os.path.exists(TESTSCRIPT):
        os.remove(TESTSCRIPT)
    if pids:
        _cmd = 'kill -9'
        for pid in pids:
            _cmd = '%s %d' % (_cmd, pid)
        run_command(_cmd)
    return

def initialize_roku(do_fix_pvr=False, msg_q=None):
    ''' initialize wintv device '''

    if msg_q:
        msg_q.put('begin initialization')

    if check_dmesg_for_ooops():
        _msg = 'signature of pvrusb2 ooops detected before unloading module,' +\
               'stopping execution immediately'
        run_command('send_to_gtalk \"%s\"' % _msg)
        kill_running_recordings(GLOBAL_LIST_OF_SUBPROCESSES)
        exit(1)

    fix_pvr_process = multiprocessing.Process(target=run_fix_pvr,\
                              args=(TURN_ON_COMMANDS, do_fix_pvr))
    fix_pvr_process.start()
    GLOBAL_LIST_OF_SUBPROCESSES.append(fix_pvr_process.pid)

    while fix_pvr_process.is_alive():
        if check_dmesg_for_ooops():
            _msg = 'signature of pvrusb2 ooops detected while unloading ' +\
                   'module, stopping execution immediately'
            run_command('send_to_gtalk \"%s\"' % _msg)
            kill_running_recordings(GLOBAL_LIST_OF_SUBPROCESSES)
            exit(1)
        time.sleep(5)

    GLOBAL_LIST_OF_SUBPROCESSES.remove(fix_pvr_process.pid)
    fix_pvr_process.join()

    if msg_q:
        msg_q.put('roku initialized')
    if LOGFILE:
        LOGFILE.write('roku initialized\n')
        LOGFILE.flush()

    return

def make_test_script(prefix='test_roku', begin_time=0):
    ''' write script to create small test video file '''
    get_lockfile()
    with open(TESTSCRIPT, 'w') as outfile:
        outfile.write('#!/bin/bash\n')
        if USE_HANDBAKE_FOR_TEST_SCRIPT:
            outfile.write('time HandBrakeCLI ')
            outfile.write('-i ~/netflix/mpg/%s_0.mpg ' % prefix)
            outfile.write('-f mp4 -e x264 -b 600 --encoder-preset ultrafast ')
            outfile.write('--start-at duration:%d ' % begin_time)
            outfile.write('--stop-at duration:10 -o ~/test.mp4 ')
            outfile.write('> ~/netflix/log/test.out 2>&1\n')
        else:
            outfile.write('time mencoder ~/netflix/mpg/%s_0.mpg ' % prefix)
            outfile.write('-ss %s -endpos 10 -ovc lavc ' % begin_time)
            outfile.write('-oac mp3lame ')
            outfile.write('-lavcopts vcodec=mpeg4:vbitrate=600:threads=2 ')
            outfile.write('-lameopts fast:preset=medium -idx -o ~/test.avi ')
            outfile.write('> ~/netflix/log/test.out 2>&1\n')
            outfile.write('mpv --ao=pcm:fast:file=/home/ddboline/test.wav ')
            outfile.write('--no-video ~/test.avi > /dev/null 2>&1\n')
            outfile.write('time HandBrakeCLI -i ~/test.avi -f mp4 -e x264 ')
            outfile.write('-b 600 -o ~/test.mp4 >> ')
            outfile.write('~/netflix/log/test.out 2>&1\n')
        outfile.write('mv ~/test.mp4 ~/public_html/videos/\n')
        outfile.write('python -c "from scripts.record_roku ')
        outfile.write('import make_audio_analysis_plots ; ')
        outfile.write('make_audio_analysis_plots(\'test.wav\', ')
        outfile.write('prefix=\'test\')"\n')
    remove_lockfile()
    return begin_time

def make_transcode_script(prefix='test_roku'):
    '''
        write out transcode file at the end of the recording,
        will be used to convert mpg to avi / mp4 later on
    '''
    bitrate = 600
    mencopts = '-ovc lavc -oac mp3lame ' +\
               '-lavcopts vcodec=mpeg4:vbitrate=%s:threads=2 ' % bitrate +\
               '-lameopts fast:preset=medium -idx'

    with open('%s/netflix/tmp/%s.sh' % (HOMEDIR, prefix), 'w') as outfile:
        outfile.write('#!/bin/bash\n')
        if USE_HANDBAKE_FOR_TRANSCODE_SCRIPT:
            outfile.write('nice -n 19 HandBrakeCLI ')
            outfile.write('-i ~/netflix/mpg/%s_0.mpg -f mp4 -e x264 ' % prefix)
            outfile.write('-b 600 --encoder-preset ultrafast ')
            outfile.write('-o ~/netflix/avi/%s.mp4 ' % prefix)
            outfile.write('> ~/netflix/log/%s.out 2>&1\n' % prefix)
        else:
            outfile.write('nice -n 19 mencoder ')
            outfile.write('~/netflix/mpg/%s_0.mpg ' % prefix)
            outfile.write('%s -vf crop=704:467:14:11,scale=470:-2 ' % mencopts)
            outfile.write('-o ~/netflix/avi/%s.avi ' % prefix)
            outfile.write('> ~/netflix/log/%s.out 2>&1\n' % prefix)
        outfile.write('mv ~/netflix/mpg/%s_0.mpg ~/tmp_avi/\n' % prefix)

def server_thread(prefix='test_roku', msg_q=None, cmd_q=None,
                  socketfile=ROKU_SOCKET_FILE):
    '''
        the server thread
        listen for requests to write thumbnail/test-script
        q, thumb, test, and time are run separately
        all others are passed to send_to_roku
    '''
    if LOGFILE:
        LOGFILE.write('starting network_thread\n')

    with OpenUnixSocketServer(socketfile) as sock:
        last_output_message = 'waiting'
        while 1:
            outstring = []
            cmd_queue = []
            with OpenSocketConnection(sock) as conn:
                for arg in conn.recv(1024).split():

                    if arg == 'q':
                        ### quit command: kill everything
                        if os.path.exists(KILLSCRIPT):
                            run_command('sh %s' % KILLSCRIPT)
                            os.remove(KILLSCRIPT)
                        sock.close()
                        return 0
                    elif arg == 'output':
                        ### output command: dump first msg_q to socket
                        if msg_q:
                            if not msg_q.empty():
                                temp = msg_q.get()
                                if temp:
                                    last_output_message = temp
                        outstring.append(last_output_message)
                    else:
                        if cmd_q:
                            ### put everything else in cmd_queue, don't do output here
                            cmd_queue.append(arg)
                if cmd_queue:
                    ### keep multicommand entries in order...
                    temp = ' '.join(cmd_queue)
                    #msg_q.put('sending command %s' % temp)
                    cmd_q.put('command %s' % temp)
                if outstring:
                    outstring = '\n'.join(outstring)
                else:
                    outstring = 'waiting'
                if LOGFILE:
                    LOGFILE.write(outstring)
                try:
                    conn.send(outstring)
                except socket.error:
                    time.sleep(10)
                    print('try again to open socket')
                    return server_thread(prefix, msg_q, cmd_q, socketfile)
    return 0

def command_thread(prefix='test_roku', msg_q=None, cmd_q=None):
    ''' independent thread to carry out commands '''
    fname = '%s/netflix/mpg/%s_0.mpg' % (HOMEDIR, prefix)
    while 1:
        if cmd_q:
            while not cmd_q.empty():
                temp = cmd_q.get()
                _cmds = ''
                if temp.find('command') == 0:
                    _cmds = temp.split()[1:]
                else:
                    cmd_q.put(temp)
                    continue

                for _cmd in _cmds:
                    outstring = ''
                    if _cmd == 'thumb':
                        if os.path.exists(fname):
                            _time = get_length_of_mpg(fname)
                            if _time > 0:
                                _ts = make_thumbnails(prefix,
                                                     begin_time=_time-1,
                                                     use_mplayer=USE_MPLAYER)
                                outstring = 'got thumbnail at t=%d %d' % (_ts,
                                            int(_ts)/60)
                            else:
                                outstring = 'ERROR: NO FILE FOUND %s' % prefix
                    elif _cmd == 'test':
                        if os.path.exists(fname):
                            _ts, _ta = make_test_file(prefix, run_script=True)
                            outstring = '%d get test movie at t=%d %d' %\
                                        (int(_ta), _ts, int(_ts)/60)
                    elif _cmd == 'time':
                        if os.path.exists(fname):
                            outstring = make_time_series_plot(fname,
                                                              prefix='test')
                    else:
                        outstring = send_to_roku([_cmd])
                        print(outstring)
                    if outstring:
                        msg_q.put(outstring)
                    time.sleep(1)
        time.sleep(1)


def make_test_file(prefix='test_roku', run_script=False):
    ''' write thumbnail and test-script at current time '''
    fname = '%s/netflix/mpg/%s_0.mpg' % (HOMEDIR, prefix)
    _time = get_length_of_mpg(fname)
    _st = -1
    if _time > 0:
        make_thumbnails(prefix, begin_time=_time-1, use_mplayer=USE_MPLAYER)
        make_test_script(prefix, _time-10)
        if run_script:
            run_command('sh %s' % TESTSCRIPT)
            try:
                _st = make_audio_analysis_plots('%s/test.wav' % HOMEDIR,
                                               prefix='test')
            except Exception:
                print('failed')
                return -1, -1
    return _time, _st


def monitoring_thread(prefix='test_roku', msg_q=None, cmd_q=None):
    '''
        seperate monitoring thread
        to periodically write out thumbnails/test-scripts
    '''
    total_time = 0
    if prefix != 'test_roku':
        sleep_time = 60
    else:
        sleep_time = 10
    while 1:
        if cmd_q:
            temp = cmd_q.get()
            if temp.find('monitor') == 0:
                sleep_time = int(temp.split()[1])
            else:
                cmd_q.put(temp)
        time.sleep(sleep_time)
        total_time += sleep_time
        if total_time == 60 or total_time == 300:
            make_test_file(prefix, run_script=True)
        else:
            make_test_file(prefix, run_script=False)
        if total_time == 300 and prefix != 'test_roku':
            if msg_q:
                msg_q.put('check_now')
            else:
                run_command('send_to_gtalk \"check_now\"')
    return 0

def start_recording(prefix='test_roku', msg_q=None, cmd_q=None):
    ''' begin recording, star control, monioring, server threads '''
    import shlex
    fname = '%s/netflix/mpg/%s_0.mpg' % (HOMEDIR, prefix)
    if USE_MPLAYER:
        _cmd = 'mplayer %s -dumpstream -dumpfile %s 2>&' % (DEVICE, fname)
    else:
        _cmd = 'mpv %s --stream-dump=%s 2>&' % (DEVICE, fname)
    if LOGFILE:
        LOGFILE.write('%s\n' % _cmd)
    args = shlex.split(_cmd)
    recording_process = subprocess.Popen(args, shell=False)
    GLOBAL_LIST_OF_SUBPROCESSES.append(recording_process.pid)
    if LOGFILE:
        LOGFILE.write('recording pid: %s\n' % recording_process.pid)
        LOGFILE.flush()

    monitoring = multiprocessing.Process(target=monitoring_thread,
                                         args=(prefix, msg_q, cmd_q,))
    monitoring.start()
    GLOBAL_LIST_OF_SUBPROCESSES.append(monitoring.pid)

    time.sleep(5)
    if not os.path.exists(fname):
        time.sleep(5)
        if not os.path.exists(fname):
            _output = 'send_to_gtalk \"RECORDING HAS NOT STARTED, ' +\
                      '%s NOT FOUND, ABORTING\"' % fname
            run_command(_output)
            kill_running_recordings(GLOBAL_LIST_OF_SUBPROCESSES)
            exit(1)
    if prefix != 'test_roku':
        _msg = 'Start recording %s' % prefix
        if msg_q:
            msg_q.put(_msg)
        else:
            run_command('send_to_gtalk \"%s\"' % _msg)
        send_to_roku(['s'])
    time.sleep(5)
    make_test_file(prefix, run_script=True)
    make_transcode_script(prefix)

    return [recording_process, monitoring]

def signal_finish(prefix='test_roku'):
    '''
        convenience function to run at end of recording time
        modifies kill file
    '''
    if prefix != 'test_roku':
        with open(KILLSCRIPT, 'a') as outfile:
            outfile.write('\n mv %s/netflix/tmp/%s.sh ' % (HOMEDIR, prefix))
            outfile.write('%s/netflix/jobs/\n' % HOMEDIR)
    _, _ta = make_test_file(prefix, run_script=True)
    run_command('send_to_gtalk \"%s is done %d\"' % (prefix, int(_ta)))
    return

def stop_recording(prefix='test_roku'):
    ''' run kill file when we stop recording '''
    run_command('send_to_gtalk \"killing %s\"' % prefix)
    if os.path.exists(KILLSCRIPT):
        run_command('sh %s ; rm %s' % (KILLSCRIPT, KILLSCRIPT))
    return

def get_lockfile(lockf=MAINLOCK):
    ''' function to obtain lockfile '''
    if lockf not in GLOBAL_LOCKFILES:
        GLOBAL_LOCKFILES[lockf] = lockfile.FileLock(lockf)
    try:
        GLOBAL_LOCKFILES[lockf].acquire(20)
    except Exception:
        GLOBAL_LOCKFILES[lockf].break_lock()
        GLOBAL_LOCKFILES[lockf].acquire()

def remove_lockfile(lockf=MAINLOCK):
    ''' function to unlock, remove lockfile '''
    if lockf in GLOBAL_LOCKFILES:
        try:
            GLOBAL_LOCKFILES[lockf].release()
        except Exception:
            return
    else:
        os.remove(lockf)

def record_roku(recording_name='test_roku', recording_time=3600,
                do_fix_pvr=False):
    '''
        main function, record video from roku device via wintv encoder
        options:
            name, duration, fix_pvr (optional),
    '''
    global DEVICE, LOGFILE
    GLOBAL_LIST_OF_SUBPROCESSES.append(os.getpid())
    DEVICE = get_dev.get_dev('pvrusb')

    LOGFILE = open('%s/netflix/log/%s_0.out' % (HOMEDIR, recording_name), 'w')
    LOGFILE.write('recording %s for %d seconds\n' % (recording_name,
                                                     recording_time))

    ### This needs to run before the server_thread is started
    if recording_name != 'test_roku':
        kill_running_recordings()
        pids = list_running_recordings(DEVICE)
        kill_running_recordings(pids)
        LOGFILE.write('killing %s \n' % pids)
    else:
        pids = list_running_recordings(DEVICE)
        if len(pids) > 0:
            print('already recording %s\n' % pids)
            LOGFILE.write('already recording %s\n' % pids)
            exit(0)

    msg_q = multiprocessing.Queue()
    cmd_q = multiprocessing.Queue()

    net = multiprocessing.Process(target=server_thread,
                                  args=(recording_name, msg_q, cmd_q,
                                        ROKU_SOCKET_FILE,))
    net.start()
    cmd = multiprocessing.Process(target=command_thread,
                                  args=(recording_name, msg_q, cmd_q,))
    cmd.start()
    GLOBAL_LIST_OF_SUBPROCESSES.extend([net.pid, cmd.pid])

    initialize_roku(do_fix_pvr, msg_q)

    rec, mon = start_recording(recording_name, msg_q, cmd_q)
    LOGFILE.flush()
    with open(KILLSCRIPT, 'w') as outfile:
        outfile.write('kill -9 %d %d %d %d %d\n' %
                (net.pid, cmd.pid, mon.pid, rec.pid, os.getpid()))

    time.sleep(recording_time)

    ### use cmd_q to change update time, not msg_q
    cmd_q.put('monitor 10')
    msg_q.put('finished recording')
    LOGFILE.write('finished recording\n')
    LOGFILE.flush()
    signal_finish(recording_name)

    if recording_name != 'test_roku':
        time.sleep(3600)

    msg_q.put('killing everything')

    LOGFILE.close()
    stop_recording(recording_name)
    GLOBAL_LIST_OF_SUBPROCESSES.remove(net.pid)
    GLOBAL_LIST_OF_SUBPROCESSES.remove(mon.pid)
    GLOBAL_LIST_OF_SUBPROCESSES.remove(rec.pid)
    GLOBAL_LIST_OF_SUBPROCESSES.remove(cmd.pid)
    mon.join()
    net.join()
    cmd.join()
    return 0
