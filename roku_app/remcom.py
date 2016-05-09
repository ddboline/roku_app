#!/usr/bin/python
''' remcom test module '''
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import argparse
import os
import time
from select import select
import multiprocessing as mp
from nose.tools import nottest

from .remove_commercials import remove_commercials
from .roku_utils import (make_thumbnails, make_audio_analysis_plots_wrapper,
                         make_time_series_plot_wrapper,
                         publish_transcode_job_to_queue, get_random_hex_string)
from .util import (run_command, send_command, OpenUnixSocketServer,
                   OpenSocketConnection, HOMEDIR)

REMCOM_SOCKET_FILE = '/tmp/.remcom_test_socket'
INPUT_DIR = '%s/Documents/movies' % HOMEDIR
OUTPUT_DIR = '/media/dileptonnas'


def remove_commercials_wrapper(input_file='', output_dir='', begin_time=0,
                               end_time=0):
    '''
        cut and splice recorded file to remove undesired sections
        (commercials), use temp not test here...
    '''
    input_string = '%d,%d' % (begin_time, end_time)
    output_file = '%s/%s' % (output_dir, os.path.basename(input_file))
    remove_commercials(input_file, output_file,
                       timing_string=input_string, do_async=True)
    return output_file


def make_video_script(input_file='', begin_time=0):
    ''' write script to create small test video file '''
    if not os.path.exists(input_file):
        return -1
    input_string = '%d,%d' % (begin_time, begin_time+10)
    tmpfile = '%s/dvdrip/tmp/test_%06x' % (HOMEDIR, get_random_hex_string(3))
    avifile = '%s.avi' % tmpfile
    mp4file = '%s.mp4' % tmpfile
    wavfile = '%s.wav' % tmpfile
    remove_commercials(infile=input_file, outfile=avifile,
                       timing_string=input_string)
    run_command('time HandBrakeCLI -i %s -f mp4 -e x264 ' % avifile +
                '-b 600 -o %s > /dev/null 2>&1\n' % mp4file)
    run_command('mpv --ao=pcm:file=%s --no-video ' % wavfile +
                '%s > /dev/null 2>&1\n' % avifile)
    run_command('mv %s %s/public_html/videos/temp.mp4\n' % (mp4file, HOMEDIR))
    run_command('du -sh %s %s/public_html/videos/temp.mp4\n' % (input_file,
                                                                HOMEDIR))
    os.remove(avifile)
    retval = make_audio_analysis_plots_wrapper(wavfile, prefix='temp')
    os.remove(wavfile)
    return retval


def make_transcode_script(input_file):
    """
        write out transcode file at the end of the recording,
        will be used to convert mpg to avi / mp4 later on
    """
    prefix = os.path.basename(input_file)
    for suffix in '.avi', '.mp4', '.mkv':
        prefix = prefix.replace(suffix, '')
    output_file = '%s/dvdrip/avi/%s.mp4' % (HOMEDIR, prefix)
    with open('%s/dvdrip/tmp/%s.sh' % (HOMEDIR, prefix), 'w') as outfile:
        outfile.write('#!/bin/bash\n')
        outfile.write('nice -n 19 HandBrakeCLI ')
        outfile.write('-i %s -o %s ' % (input_file, output_file))
        outfile.write('--preset "Android" ')
        outfile.write('> ~/dvdrip/log/%s_mp4.out 2>&1\n' % prefix)
        outfile.write('mv %s ~/Documents/movies/\n' % output_file)
        outfile.write('mv ~/dvdrip/log/%s_mp4.out ~/tmp_avi/\n' % prefix)

    os.rename('%s/dvdrip/tmp/%s.sh' % (HOMEDIR, prefix),
              '%s/dvdrip/jobs/%s.sh' % (HOMEDIR, prefix))
    return '%s/dvdrip/jobs/%s.sh' % (HOMEDIR, prefix)


def remcom(movie_filename, output_dir, begin_time, end_time,
           msg_q=None, socketfile=REMCOM_SOCKET_FILE):
    '''
        main function, takes filename, timing file as options
        communication via socket:
            q: quit remcom
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
                args = conn.recv(1024)
                if hasattr(args, 'decode'):
                    args = args.decode()
                args = args.split()

                original_end_time = end_time

                for option in args:
                    if option == 'q':
                        conn.send(b'q')
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
                        output_file = remove_commercials_wrapper(
                            movie_filename, output_dir, begin_time, end_time)
                        make_transcode_script(output_file)
                        conn.send(b'done')
                        msg_q.put('q')
                        return 0
                    elif option == 'v':
                        outstring.append('%s' % make_video_script(
                            movie_filename, begin_time=end_time))
                    elif option == 't':
                        outstring.append(
                            make_time_series_plot_wrapper(movie_filename))
                    else:
                        try:
                            end_time = int(option) * 60
                            print('end_time: %s' % option)
                        except ValueError:
                            continue
                outstring.append(
                    '%s %s %s %s' % (os.path.basename(movie_filename),
                                     '/'.join(output_dir.split('/')[-2:]),
                                     begin_time, end_time))
                tmp_begin = make_thumbnails(input_file=movie_filename,
                                            begin_time=end_time,
                                            output_dir=HOMEDIR +
                                            '/public_html/videos/'
                                            'thumbnails_tv')
                outstring.append('%d, s/f/b/q/t:' % (tmp_begin / 60))
                outstring = '\n'.join(outstring)
                conn.send(outstring.encode())

        if original_end_time > end_time:
            print('original %s new %s args %s' % (original_end_time, end_time,
                                                  args))
    return 0


def keyboard_input():
    ''' keyboard input from stdin using select function '''
    while True:
        in_, _, _ = select([os.sys.stdin], [], [], 0.1)
        if not in_:
            yield None
        else:
            for s__ in in_:
                if s__ == os.sys.stdin:
                    yield os.sys.stdin.readline()


def remcom_main(movie_filename, output_dir, begin_time, end_time):
    ''' main recom_test function '''
    msg_q = mp.Queue()

    net = mp.Process(target=remcom, args=(movie_filename, output_dir,
                                          begin_time, end_time, msg_q))
    net.start()
    time.sleep(5)

    for option in keyboard_input():
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
            run_command('kill -9 %d 2>&1 > /dev/null' % (net.pid,))
            print('killing %d' % (net.pid,))
            break
        time.sleep(0.1)
    net.join(10)


@nottest
def remcom_test_main():
    parser = argparse.ArgumentParser(description='remcom_test script')
    parser.add_argument('files', nargs='*', help='remcom_test files')
    parser.add_argument('-d', '--directory', type=str,
                        help='specify directory (must be in Documents/movies)')
    parser.add_argument('-u', '--unwatched', action='store_true',
                        help='copy to television/unwatched')
    args = parser.parse_args()

    directory = getattr(args, 'directory', None)
    unwatched = getattr(args, 'unwatched', False)
    files = getattr(args, 'files', [])
    if directory:
        if not os.path.exists(
                '%s/Documents/movies/%s' % (OUTPUT_DIR, directory)):
            raise Exception('bad directory')
        for fname in files:
            if fname.endswith('.mp4'):
                continue
            input_filename = '%s/%s' % (INPUT_DIR, fname)
            mp4_filename = fname.replace('.avi', '.mp4')
            prefix = os.path.basename(input_filename)
            for suffix in '.avi', '.mp4', '.mkv':
                prefix = prefix.replace(suffix, '')
            mp4_script = '%s/dvdrip/jobs/%s.sh' % (HOMEDIR, prefix)
            output_directory = '%s/Documents/movies/' % (OUTPUT_DIR, directory)
            remcom_main(input_filename, output_directory, 0, 0)
            if not os.path.exists(mp4_script):
                print('something bad happened %s' % input_filename)
                exit(0)
            with open(mp4_script, 'a') as inpf:
                inpf.write('cp %s/Documents/movies/%s %s/Documents/movies/'
                           '%s/\n' % (HOMEDIR, mp4_filename, OUTPUT_DIR,
                                      directory))
                inpf.write('mv %s/Documents/movies/%s/%s %s/'
                           'Documents/movies/\n' % (OUTPUT_DIR, directory,
                                                    fname, HOMEDIR))
                inpf.write('rm %s/tmp_avi/%s_0.mpg\n' % (HOMEDIR, prefix))
                inpf.write('%s/bin/make_queue add %s/Documents/movies/%s/%s\n'
                           % (HOMEDIR, OUTPUT_DIR, directory, mp4_filename))
            publish_transcode_job_to_queue(mp4_script)
    elif unwatched:
        for fname in files:
            if fname.endswith('.mp4'):
                continue
            input_filename = '%s/%s' % (INPUT_DIR, fname)
            mp4_filename = fname.replace('.avi', '.mp4')
            prefix = input_filename.split('/')[-1]
            for suffix in '.avi', '.mp4', '.mkv':
                prefix = prefix.replace(suffix, '')
            mp4_script = '%s/dvdrip/jobs/%s.sh' % (HOMEDIR, prefix)
            output_dir = '%s/television/unwatched' % OUTPUT_DIR
            remcom_main(input_filename, output_dir, 0, 0)
            if not os.path.exists(mp4_script):
                print('something bad happened %s' % input_filename)
                exit(0)
            with open(mp4_script, 'a') as inpf:
                inpf.write('cp %s/Documents/movies/%s %s/'
                           'television/unwatched/\n' % (HOMEDIR, mp4_filename,
                                                        OUTPUT_DIR))
                inpf.write('mv %s/television/unwatched/%s %s/'
                           'Documents/movies/\n' % (OUTPUT_DIR, fname,
                                                    HOMEDIR))
                inpf.write('rm %s/tmp_avi/%s_0.mpg\n' % (HOMEDIR, prefix))
                inpf.write('%s/bin/make_queue add %s/%s\n'
                           % (HOMEDIR, output_dir, mp4_filename))
            publish_transcode_job_to_queue(mp4_script)
    else:
        for fname in files:
            if fname.endswith('.mp4'):
                continue
            tmp = fname.split('.')[0].split('_')
            show = '_'.join(tmp[:-2])
            season = int(tmp[-2].strip('s'))
            episode = int(tmp[-1].strip('ep'))

            prefix = '%s_s%02d_ep%02d' % (show, season, episode)
            output_dir = '%s/Documents/television/%s/season%d' % (
                OUTPUT_DIR, show, season)
            inavifile = '%s/Documents/movies/%s.avi' % (
                HOMEDIR, prefix)
            mp4_script = '%s/dvdrip/jobs/%s.sh' % (
                HOMEDIR, prefix)
            avifile = '%s/%s.avi' % (
                output_dir, prefix)
            mp4file = '%s/Documents/movies/%s.mp4' % (
                HOMEDIR, prefix)
            mp4file_final = '%s/%s.mp4' % (
                output_dir, prefix)
            remcom_main(inavifile, output_dir, 0, 0)
            if not os.path.exists(mp4_script):
                print('something bad happened %s' % prefix)
                exit(0)
            with open(mp4_script, 'a') as inpf:
                inpf.write('mkdir -p %s\n' % output_dir)
                inpf.write('cp %s %s\n' % (mp4file, mp4file_final))
                inpf.write('mv %s %s/Documents/movies/\n' % (avifile, HOMEDIR))
                inpf.write('rm %s/tmp_avi/%s_0.mpg\n' % (HOMEDIR, prefix))
                inpf.write('%s/bin/make_queue add %s\n' % (HOMEDIR,
                                                           mp4file_final))
            publish_transcode_job_to_queue(mp4_script)
