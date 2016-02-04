# -*- coding: utf-8 -*-
"""
Utility Functions for RokuApp

Created on Fri Jun 19 17:08:47 2015

@author: ddboline
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import time
import requests

from multiprocessing import Process, Value
from subprocess import Popen, PIPE

from .util import run_command, send_command

HOMEDIR = os.getenv('HOME')
USER = os.getenv('USER')


def send_single_keypress(keypress):
    ''' wrapper around requests.post '''
#    roku_ip = '192.168.1.165'
#    roku_ip = 'roku-box.fios-router.home'
    roku_ip = 'NP-1XC384040132.fios-router.home'
    if keypress == 'Wait':
        time.sleep(5)
    elif keypress == 'Gtalk':
        run_command('%s/bin/send_to_gtalk checkRoku' % HOMEDIR)
    else:
        try:
            result = requests.post('http://%s:8060/keypress/%s' % (roku_ip,
                                                                   keypress))
        except requests.ConnectionError as exc:
            return 'connection error\n%s' % exc
        except:
            raise
        if result.status_code != 200:
            return 'Error %d on keypress %s' % (result.status_code, keypress)
    return keypress


def send_to_roku(arglist=None):
    '''
        main function, thumb and test run send message to record_roku,
        q quits, everything else sends to roku device
    '''

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
                         'as': 'Lit_*'}

    if not arglist or len(arglist) == 0:
        return retval

    for arg in arglist:
        if arg in ['thumb', 'test', 'q']:
            retval = '%s%s' % (retval, send_command(arg,
                               socketfile='/tmp/.record_roku_socket'))
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


def make_audio_analysis_plots_wrapper(infile, prefix='temp', make_plots=True,
                                      do_fft=True):
    ''' wrapper around make_audio_analysis_plots '''
    from .audio_utils import make_audio_analysis_plots
    fft_sum = Value('d')
    tmp_ = Process(target=make_audio_analysis_plots,
                   args=(infile, prefix, make_plots, do_fft, fft_sum,))
    tmp_.start()
    tmp_.join()
    return fft_sum.value


def make_time_series_plot_wrapper(input_file='', prefix='temp'):
    ''' wrapper around make_time_series_plot '''
    from .audio_utils import make_time_series_plot
    tmp_ = Process(target=make_time_series_plot, args=(input_file, prefix,))
    tmp_.start()
    tmp_.join()
    return 'Done'


def get_length_of_mpg(fname='%s/netflix/mpg/test_roku_0.mpg' % HOMEDIR):
    ''' get length of mpg/avi/mp4 with avconv '''
    if not os.path.exists(fname):
        return -1
    command = 'avconv -i %s 2>&1' % fname
    cmd_ = Popen(command, shell=True, stdout=PIPE, close_fds=True).stdout
    nsecs = 0
    for line in cmd_.readlines():
        if hasattr(line, 'decode'):
            line = line.decode()
        _line = line.split()
        if _line[0] == 'Duration:':
            items = _line[1].strip(',').split(':')
            try:
                nhour = int(items[0])
                nmin = int(items[1])
                nsecs = int(float(items[2])) + nmin*60 + nhour*60*60
            except ValueError:
                nsecs = -1
    return nsecs


def get_random_hex_string(nbytes):
    ''' use os.urandom to create n byte random string, output integer '''
    from binascii import b2a_hex
    return int(b2a_hex(os.urandom(nbytes)), 16)


def make_thumbnails(prefix='test_roku', input_file='', begin_time=0,
                    output_dir='%s/public_html/videos/thumbnails' % HOMEDIR,
                    use_mplayer=True):
    ''' write out thumbnail images from running recording at specified time '''
    tmpdir = '%s_%06x' % (output_dir, get_random_hex_string(3))

    if input_file == '':
        input_file = '%s/netflix/mpg/%s_0.mpg' % (HOMEDIR, prefix)
    if not os.path.exists(input_file):
        run_command('rm -rf %s' % tmpdir)
        return -1
    run_command('mkdir -p %s' % output_dir)
    if use_mplayer:
        run_command('mplayer -ao null -vo jpeg:outdir=%s ' % tmpdir +
                    '-frames 10 -ss %s ' % begin_time +
                    '%s 2> /dev/null > /dev/null' % input_file)
    else:
        run_command('mpv --ao=null --vo=image:format=jpg:outdir=%s ' % tmpdir +
                    '--frames=10 --start=%s ' % begin_time +
                    '%s 2> /dev/null > /dev/null' % input_file)
    run_command('mv %s/* %s/ 2> /dev/null > /dev/null' % (tmpdir, output_dir))
    run_command('rm -rf %s' % tmpdir)
    return begin_time


def write_single_line_to_file(fname, line, turn_on_commands=True):
    ''' convenience function, write single line to file then exit  '''
    if turn_on_commands:
        with open(fname, 'a') as file_:
            file_.write(line)
    else:
        print('write %s to %s' % (line, fname))


def run_fix_pvr(unload_module=True):
    '''
        unload pvrusb2, wait 10s, reload it
        fix permissions in /sys/class/pvrusb2
        hope the kernel doesn't ooops
    '''
    from .get_dev import is_module_loaded
    if unload_module:
        run_command('sudo modprobe -r pvrusb2')
        time.sleep(10)
        while is_module_loaded('pvrusb2'):
            time.sleep(10)
        run_command('sudo modprobe pvrusb2')
        time.sleep(20)
        while not is_module_loaded('pvrusb2'):
            time.sleep(10)
    run_command('sudo chown -R %s:%s ' % (USER, USER) +
                '/sys/class/pvrusb2/sn-5370885/')
    run_command('sudo chown %s:%s ' % (USER, USER) +
                '/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor')

    sdir = '/sys/class/pvrusb2/sn-5370885'

    for fn_, l__ in [['ctl_video_standard_mask_active/cur_val', 'NTSC-M'],
                     ['ctl_input/cur_val', 'composite'],
                     ['ctl_video_bitrate_mode/cur_val', 'Constant Bitrate'],
                     ['ctl_video_bitrate/cur_val', '4000000'],
                     ['ctl_volume/cur_val', '57000']]:
        write_single_line_to_file('%s/%s' % (sdir, fn_), l__)

    return


def check_dmesg_for_ooops():
    ''' check for ooops in dmesg output '''
    oops_messages = ['BUG: unable to handle kernel paging request at',
                     'general protection fault']
    cmd_ = Popen('dmesg', shell=True, stdout=PIPE, close_fds=True).stdout
    for line in cmd_.readlines():
        if hasattr(line, 'decode'):
            line = line.decode()
        if any(mes in line for mes in oops_messages):
            return True
    return False


def play_roku():
    ''' play roku '''
    import shlex
    from .get_dev import get_dev
    device = '/dev/video0'
    if check_dmesg_for_ooops():
        print('kernel has ooopsed, need to reboot')
        exit(1)
    device = get_dev('pvrusb')
    run_fix_pvr(unload_module=False)

    xcrop, ycrop, xoff, yoff = 704, 470, 14, 8

    cmd_ = 'mplayer %s -nosound ' % device + \
           '-vf crop=%d:%d:%d:%d' % (xcrop, ycrop, xoff, yoff) + \
           ',dsize=470:-2 -softvol-max 1000'

    args = shlex.split(cmd_)
    recording_process = Popen(args, shell=False)

    killscript = '%s/netflix/kill_job.sh' % HOMEDIR

    with open(killscript, 'w') as file_:
        file_.write('kill -9 %d %d\n' % (recording_process.pid, os.getpid()))

    recording_process.wait()


def open_transcode_channel():
    import pika
    parameters = pika.ConnectionParameters()
    connection = pika.BlockingConnection(parameters)

    channel = connection.channel()
    channel.queue_declare(queue='transcode_work_queue', durable=True)

    return channel


def publish_transcode_job_to_queue(script):
    import json
    assert os.path.exists(script)
    body = {'script': script}
    body = json.dumps(body)
    chan = open_transcode_channel()
    chan.basic_publish(exchange='', routing_key='transcode_work_queue',
                       body=body)
    return
