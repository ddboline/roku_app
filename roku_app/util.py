#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import socket, time
from subprocess import call, Popen, PIPE

HOMEDIR = os.getenv('HOME')

class PopenWrapperClass(object):
    def __init__(self, command):
        self.command = command

    def __enter__(self):
        self.pop_ = Popen(self.command, shell=True, stdout=PIPE,
                          close_fds=True)
        return self.pop_

    def __exit__(self, exc_type, exc_value, traceback):
        if hasattr(self.pop_, '__exit__'):
            return self.pop_.__exit__(exc_type, exc_value, traceback)
        self.pop_.wait()
        if exc_type or exc_value or traceback:
            return False
        else:
            return True

def run_command(command, do_popen=False, turn_on_commands=True,
                single_line=False):
    """ wrapper around os.system """
    if not turn_on_commands:
        print(command)
        return command
    elif do_popen:
        return PopenWrapperClass(command)
    elif single_line:
        with PopenWrapperClass(command) as pop_:
            return pop_.stdout.read()
    else:
        return call(command, shell=True)

def run_remote_command(command, is_remote=False, sshclient=None):
    ''' wrapper around os.system which also handles ssh calls '''
    if not is_remote:
        return run_command(command, do_popen=True)
    elif not sshclient:
        cmd = 'ssh %s \"%s\"' % (is_remote, command)
        print(cmd)
        return Popen(cmd, shell=True, stdout=PIPE,
                     close_fds=True).stdout.read()
    else:
        sshclient.sendline(command)
        sshclient.prompt()
        output = sshclient.before.decode()
        return output.split('\n')[1:-1]

def send_command(ostr, host='localhost', portno=10888, socketfile=None):
    ''' send string to specified socket '''
    import socket
    net_type = socket.AF_INET
    stm_type = socket.SOCK_STREAM
    addr_obj = (host, portno)
    if socketfile:
        net_type = socket.AF_UNIX
        addr_obj = socketfile

    retval = ''
    s = socket.socket(net_type, stm_type)
    try:
        s.connect(addr_obj)
    except Exception:
        print('failed to open socket')
        return False

    s.send('%s\n' % ostr)
    retval = s.recv(1024)
    s.close()
    return retval

def convert_date(input_date):
    import datetime
    _month = int(input_date[0:2])
    _day = int(input_date[2:4])
    _year = 2000 + int(input_date[4:6])
    return datetime.date(_year, _month, _day)

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

def print_h_m_s(second):
    ''' convert time from seconds to hh:mm:ss format '''
    hours = int(second / 3600)
    minutes = int(second / 60) - hours * 60
    seconds = int(second) - minutes * 60 - hours * 3600
    return '%02i:%02i:%02i' % (hours, minutes, seconds)

def print_m_s(second):
    ''' convert time from seconds to mm:ss format '''
    hours = int(second / 3600)
    minutes = int(second / 60) - hours * 60
    seconds = int(second) - minutes * 60 - hours * 3600
    if hours == 0:
        return '%02i:%02i' % (minutes, seconds)
    else:
        return '%02i:%02i:%02i' % (hours, minutes, seconds)

def run_fix_pvr(turn_on_commands=True, unload_module=True):
    '''
        unload pvrusb2, wait 10s, reload it
        fix permissions in /sys/class/pvrusb2
        hope the kernel doesn't ooops
    '''
    import time
    from get_dev import is_module_loaded
    if unload_module:
        run_command('sudo modprobe -r pvrusb2',
                    turn_on_commands=turn_on_commands)
        time.sleep(10)
        while is_module_loaded('pvrusb2'):
            time.sleep(10)
        run_command('sudo modprobe pvrusb2', turn_on_commands=turn_on_commands)
        time.sleep(20)
        while not is_module_loaded('pvrusb2'):
            time.sleep(10)
    run_command(
        'sudo chown -R ddboline:ddboline /sys/class/pvrusb2/sn-5370885/',
        turn_on_commands=turn_on_commands)
    run_command('sudo chown ddboline:ddboline ' + 
                '/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor',
                turn_on_commands=turn_on_commands)

    sdir = '/sys/class/pvrusb2/sn-5370885'

    for fn, l in [['ctl_video_standard_mask_active/cur_val', 'NTSC-M'],
                   ['ctl_input/cur_val', 'composite'],
                   ['ctl_video_bitrate_mode/cur_val', 'Constant Bitrate'],
                   ['ctl_video_bitrate/cur_val', '4000000'],
                   ['ctl_volume/cur_val', '57000']]:
        write_single_line_to_file('%s/%s' % (sdir, fn), l)

    return

oops_messages = [
    'BUG: unable to handle kernel paging request at',
    'general protection fault',
]

def check_dmesg_for_ooops():
    _cmd = Popen('dmesg', shell=True, stdout=PIPE, close_fds=True).stdout
    for l in _cmd.readlines():
        if any(mes in l for mes in oops_messages):
            return True
    return False

def write_single_line_to_file(fname, line, turn_on_commands=True):
    ''' convenience function, write single line to file then exit  '''
    if turn_on_commands:
        f = open(fname, 'a')
        f.write(line)
        f.close()
    else:
        print('write %s to %s' % (line, fname))

def datetimestring(d):
    ''' input should be datetime object, output is string '''
    if not hasattr(d, 'strftime'):
        return d
    s = d.strftime('%Y-%m-%dT%H:%M:%S%z')
    if len(s) == 24 or len(s) == 20:
        return s
    elif len(s) == 19 and 'Z' not in s:
        return '%sZ' % s

def datetimefromstring(tstr, ignore_tz=False):
    import dateutil.parser
    #tstr = tstr.replace('-05:00', '-0500').replace('-04:00', '-0400')
    #print(tstr)
    return dateutil.parser.parse(tstr, ignoretz=ignore_tz)

def make_audio_analysis_plots(infile, make_plots=True, do_fft=True,
                              prefix='temp'):
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


class OpenUnixSocketServer(object):
    def __init__(self, socketfile):
        self.sock = None
        self.socketfile = socketfile
        if os.path.exists(socketfile):
            os.remove(socketfile)
        return

    def __enter__(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            self.sock.bind(self.socketfile)
            os.chmod(self.socketfile, 0o777)
        except:
            time.sleep(10)
            print('failed to open socket')
            return self.__enter__()
        print('open socket')
        self.sock.listen(0)
        return self.sock

    def __exit__(self, exc_type, exc_value, traceback):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()
        if exc_type or exc_value or traceback:
            return False
        else:
            return True


class OpenSocketConnection(object):
    def __init__(self, sock):
        self.sock = sock

    def __enter__(self):
        self.conn, _ = self.sock.accept()
        return self.conn

    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.close()
        if exc_type or exc_value or traceback:
            return False
        else:
            return True
