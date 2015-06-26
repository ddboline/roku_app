#!/usr/bin/python
''' remcom test module '''
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import time
from select import select
import multiprocessing

from .remove_commercials import remove_commercials
from .roku_utils import (make_thumbnails, make_audio_analysis_plots_wrapper,
                         make_time_series_plot_wrapper,)
from .util import (run_command, send_command,
                   OpenUnixSocketServer, OpenSocketConnection)

REMCOM_SOCKET_FILE = '/tmp/.remcom_test_socket'
HOMEDIR = os.getenv('HOME')

def remove_commercials_wrapper(input_file='', output_dir='', begin_time=0,
                               end_time=0):
    '''
        cut and splice recorded file to remove undesired sections
        (commercials), use temp not test here...
    '''
    input_string = '%d,%d' % (begin_time, end_time)
    remove_commercials(input_file, '%s/%s' % (output_dir,
                                              input_file.split('/')[-1]),
                       timing_string=input_string)
    return 0

def make_test_script(input_file='', begin_time=0):
    ''' write script to create small test video file '''
    input_string = '%d,%d' % (begin_time, begin_time+10)
    remove_commercials(infile=input_file, outfile='%s/temp.avi' % HOMEDIR,
                       timing_string=input_string)
    run_command('time HandBrakeCLI -i %s/temp.avi -f mp4 -e x264 ' % HOMEDIR +
                '-b 600 -o %s/temp.mp4 > /dev/null 2>&1\n' % HOMEDIR)
    run_command('mpv --ao=pcm:fast:file=%s/temp.wav --no-video ' % HOMEDIR +
                '%s/temp.avi > /dev/null 2>&1\n' % HOMEDIR)
    run_command('mv %s/temp.mp4 %s/public_html/videos/temp.mp4\n'
                % (HOMEDIR, HOMEDIR))
    os.remove('%s/temp.avi' % HOMEDIR)
    return make_audio_analysis_plots_wrapper('%s/temp.wav' % HOMEDIR,
                                             prefix='temp')


def remcom_test(movie_filename, output_dir, begin_time, end_time,
                msg_q=None, socketfile=REMCOM_SOCKET_FILE):
    '''
        main function, takes filename, timing file as options
        communication via socket:
            q: quit remcom_test
            f: move forward, number of minutes can be included, i.e.
                f5 moves forward 5 minues
            b: move backwards... b5 moves backwards 5 minutes
            s: select
            v: test video
            t: thumbnail

    '''
    with OpenUnixSocketServer(socketfile) as sock:
        while True:
            outstring = []
            with OpenSocketConnection(sock) as conn:
                args = conn.recv(1024).split()

                original_end_time = end_time

                print(args)

                for option in args:
                    if option == 'q':
                        conn.send('q')
                        msg_q.put('q')
                        return 0
                    elif option[0] == 'f':
                        try:
                            end_time += int(option[1:]) * 60
                        except ValueError:
                            end_time += 60
                    elif option[0] == 'b':
                        try:
                            end_time -= int(option[1:]) * 60
                        except ValueError:
                            end_time -= 60
                    elif option == 's':
                        remove_commercials_wrapper(movie_filename, output_dir,
                                                   begin_time, end_time)
                        conn.send('done')
                        msg_q.put('q')
                        return 0
                    elif option == 'v':
                        outstring.append(
                            '%s' % make_test_script(movie_filename,
                                                    begin_time=end_time))
                    elif option == 't':
                        outstring.append(
                            make_time_series_plot_wrapper(movie_filename))
                    else:
                        try:
                            end_time = int(option) * 60
                            print('set end_time to %s %s' % (option,
                                                             type(option)))
                        except ValueError:
                            continue
                outstring.append(
                    '%s %s %s %s' % (movie_filename.split('/')[-1],
                                     '/'.join(output_dir.split('/')[-2:]),
                                     begin_time, end_time))
                tmp_begin = make_thumbnails(
                            input_file=movie_filename, begin_time=end_time,
                            output_dir='%s/public_html/videos/thumbnails_tv'
                                       % HOMEDIR)
                outstring.append('%d, s/f/b/q/t:' % (tmp_begin / 60))
                conn.send('\n'.join(outstring))

        if original_end_time > end_time:
            print('original %s new %s args %s' % (original_end_time, end_time,
                                                  args))
    return 0

def keyboard_input():
    ''' keyboard input from stdin using select function '''
    in_, _, _ = select([os.sys.stdin], [], [], 0.0001)
    for s__ in in_:
        if s__ == os.sys.stdin:
            return os.sys.stdin.readline()
    return None

def remcom_test_main(movie_filename, output_dir, begin_time, end_time):
    ''' main recom_test function '''
    msg_q = multiprocessing.Queue()

    net = multiprocessing.Process(target=remcom_test,
                                  args=(movie_filename, output_dir,
                                        begin_time, end_time, msg_q))
    net.start()
    time.sleep(5)

    option = None
    while True:
        option = keyboard_input()
        if option:
            option = send_command(option, socketfile=REMCOM_SOCKET_FILE)
            if option:
                print(option,)
                os.sys.stdout.flush()
            option = False
        while not msg_q.empty():
            option = msg_q.get()
            print('got message %s' % option)
        if option == 'q':
            run_command('kill -9 %d %d 2>&1 > /dev/null' % (net.pid,
                                                            os.getpid()))
            print('killing %d %d' % (net.pid, os.getpid()))
            break
        time.sleep(1)
    net.join(10)
