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
import time
import requests

from multiprocessing import Process
from subprocess import Popen, PIPE

from .util import run_command, send_command

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

def make_audio_analysis_plots(infile, prefix='temp', make_plots=True,
                              do_fft=True):
    import numpy as np
    from scipy import fftpack
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as pl
    from scipy.io import wavfile

    try:
        rate, data = wavfile.read(infile)
    except ValueError:
        return -1
    dt = 1./rate
    T = dt * data.shape[0]
    tvec = np.arange(0, T, dt)
    sig0 = data[:, 0]
    sig1 = data[:, 1]
    if not do_fft:
        return float(np.sum(np.abs(sig0)))
    if make_plots:
        pl.clf()
        pl.plot(tvec, sig0)
        pl.plot(tvec, sig1)
        xtickarray = range(0, 12, 2)
        pl.xticks(xtickarray, ['%d s' % x for x in xtickarray])
        pl.savefig('%s/%s_time.png' % (HOMEDIR, prefix))
        pl.clf()
    samp_freq0 = fftpack.fftfreq(sig0.size, d=dt)
    sig_fft0 = fftpack.fft(sig0)
    samp_freq1 = fftpack.fftfreq(sig1.size, d=dt)
    sig_fft1 = fftpack.fft(sig1)
    if make_plots:
        pl.clf()
        pl.plot(np.log(np.abs(samp_freq0)+1e-9), np.abs(sig_fft0))
        pl.plot(np.log(np.abs(samp_freq1)+1e-9), np.abs(sig_fft1))
        pl.xlim(np.log(10), np.log(40e3))
        xtickarray = np.log(np.array([20, 1e2, 3e2, 1e3, 3e3, 10e3, 30e3]))
        pl.xticks(xtickarray, ['20Hz', '100Hz', '300Hz', '1kHz', '3kHz',
                               '10kHz', '30kHz'])
        pl.savefig('%s/%s_fft.png' % (HOMEDIR, prefix))
        pl.clf()

        run_command('mv %s/%s_time.png %s/%s_fft.png %s/public_html/videos/'
                    % (HOMEDIR, prefix, HOMEDIR, prefix, HOMEDIR))

    return float(np.sum(np.abs(sig_fft0)))

def make_audio_analysis_plots_wrapper(infile, prefix='temp', make_plots=True,
                              do_fft=True):
    tmp_ = Process(target=make_audio_analysis_plots,
                  args=(infile, prefix, make_plots, do_fft,))
    tmp_.start()
    tmp_.join()

def make_time_series_plot(input_file='', prefix='temp'):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as pl

    length_of_file = get_length_of_mpg(input_file)
    audio_vals = []
    for t in range(0,length_of_file, 60):
        run_command('mpv --start=%d ' % t + 
                    '--length=10 --ao=pcm:fast:file=%s/' % HOMEDIR +
                    '%s.wav --no-video ' % prefix + 
                    '%s 2> /dev/null > /dev/null' % input_file)
        aud_int = make_audio_analysis_plots('%s/%s.wav' % (HOMEDIR, prefix),
                                            make_plots=False, do_fft=False)
        audio_vals.append(aud_int)
    #print(audio_vals)
    x = np.arange(0, length_of_file, 60)
    y = np.array(audio_vals)
    pl.clf()
    pl.plot(x/60., y)
    pl.savefig('%s/%s_time.png' % (HOMEDIR, prefix))
    pl.clf()
    run_command('mv %s/%s_time.png %s/public_html/videos/' % (HOMEDIR, prefix,
                                                              HOMEDIR))
    return 'Done'

def make_time_series_plot_wrapper(input_file='', prefix='temp'):
    tmp_ = Process(target=make_time_series_plot, args=(input_file, prefix,))
    tmp_.start()
    tmp_.join()
    return 'Done'

def get_length_of_mpg(fname='%s/netflix/mpg/test_roku_0.mpg' % HOMEDIR):
    ''' get length of mpg/avi/mp4 with avconv '''
    if not os.path.exists(fname):
        return -1
    command = 'avconv -i %s 2>&1' % fname
    _cmd = Popen(command, shell=True, stdout=PIPE, close_fds=True).stdout
    nsecs = 0
    for line in _cmd.readlines():
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

def get_random_hex_string(n):
    ''' use os.urandom to create n byte random string, output integer '''
    from binascii import b2a_hex
    return int(b2a_hex(os.urandom(n)), 16)

def make_thumbnails(prefix='test_roku', input_file='', begin_time=0,
                    output_dir='%s/public_html/videos/thumbnails' % HOMEDIR,
                    use_mplayer=True):
    ''' write out thumbnail images from running recording at specified time '''
    TMPDIR = '%s_%06x' % (output_dir, get_random_hex_string(3))

    if input_file == '':
        input_file = '%s/netflix/mpg/%s_0.mpg' % (HOMEDIR, prefix)
    if not os.path.exists(input_file):
        run_command('rm -rf %s' % TMPDIR)
        return -1
    run_command('mkdir -p %s' % output_dir)
    if use_mplayer:
        run_command('mplayer -ao null -vo jpeg:outdir=%s ' % TMPDIR + 
                    '-frames 10 -ss %s ' % begin_time + 
                    '%s 2> /dev/null > /dev/null' % input_file)
    else:
        run_command('mpv --ao=null --vo=image:format=jpg:outdir=%s ' % TMPDIR +
                    '--frames=10 --start=%s ' % begin_time +
                    '%s 2> /dev/null > /dev/null' % input_file)
    run_command('mv %s/* %s/ 2> /dev/null > /dev/null' % (TMPDIR, output_dir))
    run_command('rm -rf %s' % TMPDIR)
    return begin_time

def write_single_line_to_file(fname, line, turn_on_commands=True):
    ''' convenience function, write single line to file then exit  '''
    if turn_on_commands:
        f = open(fname, 'a')
        f.write(line)
        f.close()
    else:
        print('write %s to %s' % (line, fname))

def run_fix_pvr(unload_module=True):
    '''
        unload pvrusb2, wait 10s, reload it
        fix permissions in /sys/class/pvrusb2
        hope the kernel doesn't ooops
    '''
    import time
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
    run_command(
        'sudo chown -R ddboline:ddboline /sys/class/pvrusb2/sn-5370885/')
    run_command('sudo chown ddboline:ddboline ' + 
                '/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor')

    sdir = '/sys/class/pvrusb2/sn-5370885'

    for fn, l in [['ctl_video_standard_mask_active/cur_val', 'NTSC-M'],
                   ['ctl_input/cur_val', 'composite'],
                   ['ctl_video_bitrate_mode/cur_val', 'Constant Bitrate'],
                   ['ctl_video_bitrate/cur_val', '4000000'],
                   ['ctl_volume/cur_val', '57000']]:
        write_single_line_to_file('%s/%s' % (sdir, fn), l)

    return

def check_dmesg_for_ooops():
    oops_messages = ['BUG: unable to handle kernel paging request at',
                     'general protection fault',]
    _cmd = Popen('dmesg', shell=True, stdout=PIPE, close_fds=True).stdout
    for l in _cmd.readlines():
        if any(mes in l for mes in oops_messages):
            return True
    return False

def play_roku():
    import shlex
    from .get_dev import get_dev
    device = '/dev/video0'
    if check_dmesg_for_ooops():
        print('kernel has ooopsed, need to reboot')
        exit(1)
    device = get_dev('pvrusb')
    run_fix_pvr(unload_module=False)

    XCROP, YCROP, XOFF, YOFF = 704, 470, 14, 8

    _cmd = 'mplayer %s -nosound ' % device + \
           '-vf crop=%d:%d:%d:%d' % (XCROP, YCROP, XOFF, YOFF) + \
           ',dsize=470:-2 -softvol-max 1000'

    args = shlex.split(_cmd)
    recording_process = Popen(args, shell=False)

    killscript = '%s/netflix/kill_job.sh' % HOMEDIR

    f = open(killscript, 'w')
    f.write('kill -9 %d %d\n' % (recording_process.pid, os.getpid()))
    f.close()

    recording_process.wait()

