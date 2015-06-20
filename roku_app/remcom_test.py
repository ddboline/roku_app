#!/usr/bin/python
from __future__ import print_function

import os
import time
import select
from util import run_command, make_thumbnails, send_command, \
                  make_audio_analysis_plots, make_time_series_plot, \
                  OpenUnixSocketServer, OpenSocketConnection
import multiprocessing

TURN_ON_COMMANDS = True
REMCOM_SOCKET_FILE = '/tmp/.remcom_test_socket'
HOMEDIR = os.getenv('HOME')

def remove_commercials_wrapper(input_file='', output_dir='', begin_time=0,
                               end_time=0):
    '''
        cut and splice recorded file to remove undesired sections
        (commercials), use temp not test here...
    '''
    import remove_commercials
    INPUT_STRING = '%d,%d' % (begin_time, end_time)
    remove_commercials.remove_commercials(input_file,
                                      '%s/%s' % (output_dir,
                                      input_file.split('/')[-1]),
                                      TIMING_STRING=INPUT_STRING)
    return 0

def make_test_script(input_file='', begin_time=0):
    ''' write script to create small test video file '''
    import remove_commercials
    INPUT_STRING = '%d,%d' % (begin_time, begin_time+10)
    remove_commercials.remove_commercials(INFILE=input_file,
                                          OUTFILE='%s/temp.avi'
                                          % HOMEDIR,
                                          TIMING_STRING=INPUT_STRING)
    run_command('time HandBrakeCLI -i %s/temp.avi -f mp4 -e x264 ' % HOMEDIR +
                '-b 600 -o %s/temp.mp4 > /dev/null 2>&1\n' % HOMEDIR)
    run_command('mpv --ao=pcm:fast:file=%s/temp.wav --no-video ' % HOMEDIR +
                '%s/temp.avi > /dev/null 2>&1\n' % HOMEDIR)
    run_command('mv %s/temp.mp4 %s/public_html/videos/temp.mp4\n'
                % (HOMEDIR, HOMEDIR))
    os.remove('%s/temp.avi' % HOMEDIR)
    return make_audio_analysis_plots('%s/temp.wav' % HOMEDIR, prefix='temp')


def remcom_test(movie_filename, output_dir, begin_time, end_time,
                socketfile=REMCOM_SOCKET_FILE, msg_q=None):
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
                        outstring.append(make_time_series_plot(movie_filename))
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
    i, o, e = select.select([os.sys.stdin], [], [], 0.0001)
    for s in i:
        if s == os.sys.stdin:
            return os.sys.stdin.readline()
    return None

def remcom_test_main(movie_filename, output_dir, begin_time, end_time):

    msg_q = multiprocessing.Queue()

    net = multiprocessing.Process(target=remcom_test,
                                  args=(movie_filename, output_dir,
                                        _begin_time, _end_time,
                                        REMCOM_SOCKET_FILE, msg_q))
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

if __name__ == '__main__':
    if len(os.sys.argv) > 4:
        movie_filename = os.sys.argv[1]
        output_dir = os.sys.argv[2]
        _begin_time = int(os.sys.argv[3])
        _end_time = int(os.sys.argv[4])
    else:
        print('python remcom_test.py <file> <dir> <begin> <end>')
        exit(0)

    remcom_test_main(movie_filename, output_dir, _begin_time, _end_time)
