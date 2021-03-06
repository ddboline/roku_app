#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Script to record from roku device via WinTV HVR-1950
"""
from __future__ import print_function

import os
import time
from subprocess import Popen
from multiprocessing import Queue, Process, cpu_count
import socket
import logging

from .get_dev import get_dev
from .roku_utils import (make_audio_analysis_plots_wrapper, make_time_series_plot_wrapper,
                         run_fix_pvr, check_dmesg_for_ooops, get_length_of_mpg, make_thumbnails,
                         send_to_roku, get_random_hex_string)
from .util import (
    run_command,
    OpenUnixSocketServer,
    OpenSocketConnection,
)

### Global variables, immutable
HOMEDIR = os.getenv('HOME')
TEMPDIR = '%s/netflix/tmp'
TESTSCRIPT = '%s/netflix/test.sh' % HOMEDIR
KILLSCRIPT = '%s/netflix/kill_job.sh' % HOMEDIR
GLOBAL_LIST_OF_SUBPROCESSES = []
NCPU = cpu_count()


def list_running_recordings(devname='/dev/video0'):
    """ list any currently running recordings """
    pids = []
    parents = []
    lines = []
    with run_command('ps -eF 2> /dev/null', do_popen=True) as pop_:
        for line in pop_:
            lines.append(line)
    for line in lines:
        if devname in line:
            ents = line.strip().split()
            pids.append(int(ents[1]))
            parents.append(int(ents[2]))
    for line in lines:
        if 'run_recording' in line:
            ents = line.strip().split()
            pid = int(ents[1])
            parent = int(ents[2])
            if pid in parents or parent in parents:
                pids.append(pid)
    return pids


def kill_running_recordings(pids=None):
    """ kill list of pids """
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
    """ initialize wintv device """

    if msg_q:
        msg_q.put('begin initialization')

    if check_dmesg_for_ooops():
        _msg = 'signature of pvrusb2 ooops detected before ' +\
               'unloading module, stopping execution immediately'
        run_command('send_to_gtalk \"%s\"' % _msg)
        kill_running_recordings(GLOBAL_LIST_OF_SUBPROCESSES)
        exit(1)

    fix_pvr_process = Process(target=run_fix_pvr, args=(do_fix_pvr, ))
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
    logging.info('roku initialized\n')

    return


def make_video(prefix='test_roku', begin_time=0):
    """ write video file, then run audio analysis on it """
    tmpfile = '%s/netflix/tmp/test_%06x' % (HOMEDIR, get_random_hex_string(3))
    cmd_ = 'time mencoder ~/netflix/mpg/%s_0.mpg ' % prefix + \
           '-ss %s -endpos 10 -ovc lavc ' % begin_time + \
           '-oac mp3lame ' + \
           '-lavcopts vcodec=mpeg4:vbitrate=600:threads=%s ' % NCPU + \
           '-lameopts fast:preset=medium -idx -o %s.avi ' % tmpfile + \
           '> ~/netflix/log/test.out 2>&1'
    run_command(cmd_)
    cmd_ = 'mpv --ao=pcm:file=%s.wav ' % tmpfile + \
           '--no-video %s.avi > /dev/null 2>&1' % tmpfile
    run_command(cmd_)
    ### matplotlib apparently occupies ~80MB in RAM
    ### running in a separate process ensures that the memory is released...
    result = make_audio_analysis_plots_wrapper('%s.wav' % tmpfile, prefix='test')
    cmd_ = 'time HandBrakeCLI -i %s.avi -f mp4 -e x264 ' % tmpfile + \
           '-b 600 -o %s.mp4 >> ' % tmpfile + \
           '~/netflix/log/test.out 2>&1'
    run_command(cmd_)
    run_command('mv %s.mp4 ~/public_html/videos/test.mp4' % tmpfile)
    run_command('cp ~/public_html/videos/test.mp4 ' '~/public_html/videos/AAAAAAA/')
    run_command('rm %s.*' % tmpfile)

    return result


def make_transcode_script(prefix='test_roku', use_handbrake_for_transcode=False):
    """
        write out transcode file at the end of the recording,
        will be used to convert mpg to avi / mp4 later on
    """
    bitrate = 600
    mencopts = '-ovc lavc -oac mp3lame ' +\
               '-lavcopts vcodec=mpeg4:vbitrate=%s:' % bitrate +\
               'threads=%s -lameopts fast:preset=medium -idx' % NCPU

    outfile = '%s/netflix/tmp/%s.sh' % (HOMEDIR, prefix)

    with open(outfile, 'w') as outfile:
        outfile.write('#!/bin/bash\n')
        if use_handbrake_for_transcode:
            outfile.write('nice -n 19 HandBrakeCLI ')
            outfile.write('-i ~/netflix/mpg/%s_0.mpg -f mp4 -e x264 ' % prefix)
            outfile.write('-b 600 --encoder-preset ultrafast ')
            outfile.write('-o ~/netflix/avi/%s.mp4 ' % prefix)
            outfile.write('> ~/netflix/log/%s.out 2>&1\n' % prefix)
            outfile.write('mv ~/netflix/avi/%s.mp4 ~/Documents/movies/\n ' % prefix)
        else:
            outfile.write('nice -n 19 mencoder ')
            outfile.write('~/netflix/mpg/%s_0.mpg ' % prefix)
            outfile.write('%s -vf crop=704:467:14:11,scale=470:-2 ' % mencopts)
            outfile.write('-o ~/netflix/avi/%s.avi ' % prefix)
            outfile.write('> ~/netflix/log/%s.out 2>&1\n' % prefix)
            outfile.write('mv ~/netflix/avi/%s.avi ~/Documents/movies/\n' % prefix)
        outfile.write('mv ~/netflix/log/%s.out ~/tmp_avi/\n' % prefix)
        outfile.write('mv ~/netflix/mpg/%s_0.mpg ~/tmp_avi/\n' % prefix)
    return outfile


def server_thread(prefix='test_roku', msg_q=None, cmd_q=None,
                  socketfile='/tmp/.record_roku_socket'):
    """
        the server thread
        listen for requests to write thumbnail/test-script
        q, thumb, test, and time are run separately
        all others are passed to send_to_roku
    """
    logging.info('starting network_thread\n')

    with OpenUnixSocketServer(socketfile) as sock:
        last_output_message = 'waiting'
        while 1:
            outstring = []
            cmd_queue = []
            with OpenSocketConnection(sock) as conn:
                for arg in conn.recv(1024).split():
                    if hasattr(arg, 'decode'):
                        arg = arg.decode()
                    if arg == 'q':
                        ### quit command: kill everything
                        if os.path.exists(KILLSCRIPT):
                            run_command('sh %s ; rm %s' % (KILLSCRIPT, KILLSCRIPT))
                        return 0
                    else:
                        ### output command: dump first msg_q to socket
                        if msg_q:
                            if not msg_q.empty():
                                temp = msg_q.get()
                                if temp:
                                    last_output_message = temp
                        outstring.append(last_output_message)
                        if cmd_q:
                            cmd_queue.append(arg)
                if cmd_queue:
                    temp = ' '.join(cmd_queue)
                    cmd_q.put('command %s' % temp)
                if outstring:
                    outstring = '\n'.join(outstring)
                else:
                    outstring = last_output_message
                logging.info(outstring)
                try:
                    if hasattr(outstring, 'encode'):
                        outstring = outstring.encode()
                    conn.send(outstring)
                except socket.error:
                    time.sleep(10)
                    print('try again to open socket')
                    return server_thread(prefix, msg_q, cmd_q, socketfile)
    return 0


def command_thread(prefix='test_roku', msg_q=None, cmd_q=None):
    """ independent thread to carry out commands """
    fname = '%s/netflix/mpg/%s_0.mpg' % (HOMEDIR, prefix)
    while 1:
        if cmd_q:
            while not cmd_q.empty():
                temp = cmd_q.get()
                _cmds = ''
                if temp.startswith('command'):
                    _cmds = temp.split()[1:]
                else:
                    continue

                for _cmd in _cmds:
                    outstring = ''
                    if _cmd == 'thumb':
                        if os.path.exists(fname):
                            _time = get_length_of_mpg(fname)
                            if _time > 0:
                                _ts = make_thumbnails(prefix, begin_time=_time - 1)
                                outstring = 'got thumbnail at t=%d %d' % (_ts, int(_ts) / 60)
                            else:
                                outstring = 'ERROR: NO FILE FOUND %s' % prefix
                    elif _cmd == 'test':
                        if os.path.exists(fname):
                            _ts, _ta = make_thumb_script(prefix)
                            outstring = '%d get test movie at t=%d %d' %\
                                        (int(_ta), _ts, int(_ts)/60)
                    elif _cmd == 'time':
                        if os.path.exists(fname):
                            outstring = make_time_series_plot_wrapper(fname, prefix='test')
                    elif _cmd == 'extend':
                        msg_q.put('extend')
                    elif _cmd != 'output':
                        outstring = send_to_roku([_cmd])
                    if outstring:
                        msg_q.put(outstring)
                    time.sleep(1)
        time.sleep(1)


def make_thumb_script(prefix='test_roku'):
    """ write thumbnail and test-script at current time """
    fname = '%s/netflix/mpg/%s_0.mpg' % (HOMEDIR, prefix)

    if not os.path.exists(fname):
        return -1, -1

    time_ = get_length_of_mpg(fname)

    st_ = -1
    if time_ > 0:
        make_thumbnails(prefix, begin_time=time_ - 1)

        st_ = make_video(prefix, time_ - 10)

    return time_, st_


def monitoring_thread(prefix='test_roku', msg_q=None, mon_q=None):
    """
        seperate monitoring thread
        to periodically write out thumbnails/test-scripts
    """
    total_time = 0
    if prefix != 'test_roku':
        sleep_time = 60
    else:
        sleep_time = 10
    while 1:
        if mon_q:
            temp = mon_q.get()
            if temp.startswith('monitor'):
                sleep_time = int(temp.split()[1])
        time.sleep(sleep_time)
        total_time += sleep_time
        if total_time == 60 or total_time == 300:
            make_thumb_script(prefix)
        else:
            make_thumb_script(prefix)
        if total_time == 300 and prefix != 'test_roku':
            if msg_q:
                msg_q.put('check_now')
            else:
                run_command('send_to_gtalk \"check_now\"')
    return 0


def start_recording(device='/dev/video0',
                    prefix='test_roku',
                    msg_q=None,
                    mon_q=None,
                    use_mplayer=True):
    """ begin recording, star control, monioring, server threads """
    import shlex
    fname = '%s/netflix/mpg/%s_0.mpg' % (HOMEDIR, prefix)
    if use_mplayer:
        _cmd = 'mplayer %s -dumpstream -dumpfile %s 2>&' % (device, fname)
    else:
        _cmd = 'mpv %s --stream-dump=%s 2>&' % (device, fname)
    logging.info('%s\n', _cmd)
    args = shlex.split(_cmd)

    recording_process = Popen(args, shell=False)
    GLOBAL_LIST_OF_SUBPROCESSES.append(recording_process.pid)
    logging.info('recording pid: %s\n', recording_process.pid)

    monitoring = Process(
        target=monitoring_thread, args=(
            prefix,
            msg_q,
            mon_q,
        ))
    monitoring.start()

    GLOBAL_LIST_OF_SUBPROCESSES.append(monitoring.pid)

    time.sleep(5)
    if not os.path.exists(fname):
        time.sleep(5)
        if not os.path.exists(fname):
            _output = 'send_to_gtalk \"RECORDING HAS NOT STARTED, ' + \
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

    make_thumb_script(prefix)

    make_transcode_script(prefix)

    return [recording_process, monitoring]


def signal_finish(prefix='test_roku'):
    """
        convenience function to run at end of recording time
        modifies kill file
    """
    if prefix != 'test_roku':
        with open(KILLSCRIPT, 'a') as outfile:
            outfile.write('\n mv %s/netflix/tmp/%s.sh ' % (HOMEDIR, prefix))
            outfile.write('%s/netflix/jobs/\n' % HOMEDIR)
            outfile.write('cd ~/setup_files/build/roku_app/ ; '
                          'python -c "import roku_app.roku_utils ; '
                          'roku_app.roku_utils.publish_transcode_job_to_queue('
                          "'%s/netflix/jobs/%s.sh'" % (HOMEDIR, prefix) + ')"\n')

    _, _ta = make_thumb_script(prefix)
    run_command('send_to_gtalk \"%s is done %d\"' % (prefix, int(_ta)))
    return


def stop_recording(prefix='test_roku'):
    """ run kill file when we stop recording """
    run_command('send_to_gtalk \"killing %s\"' % prefix)
    if os.path.exists(KILLSCRIPT):
        run_command('sh %s ; rm %s' % (KILLSCRIPT, KILLSCRIPT))
    return


def record_roku(recording_name='test_roku', recording_time=3600, do_fix_pvr=False):
    """
        main function, record video from roku device via wintv encoder
        options:
            name, duration, fix_pvr (optional),
    """
    GLOBAL_LIST_OF_SUBPROCESSES.append(os.getpid())
    device = get_dev('pvrusb')

    logging.info('recording %s for %d seconds\n', recording_name, recording_time)

    ### This needs to run before the server_thread is started
    if recording_name != 'test_roku':
        kill_running_recordings()
        pids = list_running_recordings(device)
        kill_running_recordings(pids)
        logging.info('killing %s \n', pids)
    else:
        pids = list_running_recordings(device)
        if len(pids) > 0:
            print('already recording %s\n' % pids)
            logging.error('already recording %s\n', pids)
            exit(0)

    msg_q = Queue()
    cmd_q = Queue()
    mon_q = Queue()

    net = Process(
        target=server_thread, args=(
            recording_name,
            msg_q,
            cmd_q,
        ))
    net.start()

    cmd = Process(
        target=command_thread, args=(
            recording_name,
            msg_q,
            cmd_q,
        ))
    cmd.start()
    GLOBAL_LIST_OF_SUBPROCESSES.extend([net.pid, cmd.pid])

    initialize_roku(do_fix_pvr, msg_q)

    rec, mon = start_recording(device, recording_name, msg_q, mon_q)
    with open(KILLSCRIPT, 'w') as outfile:
        outfile.write('kill -9 %d %d %d %d %d\n' % (net.pid, cmd.pid, mon.pid, rec.pid,
                                                    os.getpid()))

    time.sleep(recording_time)

    ### use cmd_q to change update time, not msg_q
    mon_q.put('monitor 10')
    msg_q.put('finished recording')
    logging.info('finished recording\n')
    signal_finish(recording_name)

    if recording_name != 'test_roku':
        time.sleep(3600)

    msg_q.put('killing everything')

    stop_recording(recording_name)
    GLOBAL_LIST_OF_SUBPROCESSES.remove(net.pid)
    GLOBAL_LIST_OF_SUBPROCESSES.remove(mon.pid)
    GLOBAL_LIST_OF_SUBPROCESSES.remove(rec.pid)
    GLOBAL_LIST_OF_SUBPROCESSES.remove(cmd.pid)
    mon.join()
    net.join()
    cmd.join()
    return 0


def main():
    from sys import argv

    recording_name = 'test_roku'
    recording_time = 3600
    do_fix_pvr = False

    if len(argv) > 1:
        recording_name = argv[1]
    if len(argv) > 2:
        try:
            recording_time = int(argv[2]) * 60
        except ValueError:
            pass
    if len(argv) > 3:
        if argv[3] == 'fix_pvr':
            do_fix_pvr = True

    record_roku(recording_name, recording_time, do_fix_pvr)
