#! /usr/bin/env python
# -*- coding: utf-8 -*-
""" extract mpg from dvd, write encoding script """
from __future__ import print_function

import os
from roku_app.roku_utils import publish_transcode_job_to_queue
from roku_app.util import run_command

HOMEDIR = os.getenv('HOME')
DIR = '%s/dvdrip' % HOMEDIR
DEBUG = False


def make_encoding_file(name):
    """
        write out transcode file after dumping dvd to vob,
        will be used to convert vob to mp4 later on
    """
    input_file = '%s/vob/%s.vob' % (DIR, name)
    output_file = '%s/dvdrip/avi/%s.mp4' % (HOMEDIR, name)
    with open('%s/dvdrip/tmp/%s.sh' % (HOMEDIR, name), 'w') as outfile:
        outfile.write('#!/bin/bash\n')
        outfile.write('nice -n 19 HandBrakeCLI ')
        outfile.write('-i %s -o %s ' % (input_file, output_file))
        outfile.write('--preset "Android" ')
        outfile.write('--subtitle-burned ')
        outfile.write('> ~/dvdrip/log/%s_dvd.out 2>&1\n' % name)
        outfile.write('mv %s ~/tmp_avi/\n' % input_file)
        outfile.write('mv ~/dvdrip/log/%s_dvd.out ~/tmp_avi/\n' % name)
        outfile.write('mv %s ~/Documents/movies/\n' % output_file)
    os.rename('%s/dvdrip/tmp/%s.sh' % (HOMEDIR, name),
              '%s/dvdrip/jobs/%s.sh' % (HOMEDIR, name))
    publish_transcode_job_to_queue('%s/dvdrip/jobs/%s.sh' % (HOMEDIR, name))


def read_dvd():
    """ run lsdvd """
    command = run_command('lsdvd /dev/sr0', do_popen=True)
    for line in command:
        items = line.split()
        if len(items) == 0 or items[0] != 'Title:':
            continue
        print(line.strip())


def run_extracting(title, chapter, name, aid, sid=-1, donav=False):
    """
        dump vob file from dvd, specify title, chapter,
        prefix of resulting file, audio language (aid),
        subtitle language (sid), and whether to use dvdnav
    """
    sid_val = 0
    dvd = 'dvd'
    if donav:
        dvd = 'dvdnav'
    if sid < 0:
        command = 'mpv %s://%i --dvd-device=/dev/sr0 ' % (dvd, title,) + \
                  '--chapter=%i ' % chapter + \
                  '--stream-dump=%s/vob/%s.vob ' % (DIR, name,) + \
                  '--aid=%i ' % aid
    else:
        command = 'mpv %s://%i --dvd-device=/dev/sr0  ' % (dvd, title,) + \
                  '--chapter=%i ' % chapter + \
                  '--stream-dump=%s/vob/%s.vob ' % (DIR, name,) + \
                  '--aid=%i --sid=%i ' % (aid, sid_val,)
    if donav:
        command = '%s ' % command

    if DEBUG:
        print(title, chapter, name, aid, sid)
    run_command(command)

    make_encoding_file(name)

    return 0


def make_dvdextract():
    """ main function, handles input from the stdin """
    name = ''
    title = 0
    chapter = 0
    aid = 128
    sid = -1
    donav = False

    if len(os.sys.argv) > 1:
        if os.sys.argv[1].count('nav') == 1:
            donav = True
        if os.sys.argv[1][0] == 'h':
            print('make_dvdextract <read,run,runnav,rm,file,filenav,avi,' +
                  'avinav> <name> <title> <chapter> <aid=> <sid=>')
            return 0
        elif os.sys.argv[1][0:3] == 'run' and len(os.sys.argv) > 2:
            name = os.sys.argv[2]
            if len(os.sys.argv) > 3:
                for arg in os.sys.argv[3:]:
                    cmd, ent = arg.split('=')
                    if cmd == 'aid':
                        aid = int(ent)
                    elif cmd == 'sid':
                        sid = int(ent)
                    elif cmd == 'title' or cmd == 'tit':
                        title = int(ent)
                    elif cmd == 'chapter' or cmd == 'chap':
                        chapter = int(ent)
            return run_extracting(title, chapter, name, aid, sid, donav)
        elif os.sys.argv[1][0:3] == 'avi' and len(os.sys.argv) > 2:
            name = os.sys.argv[2]
            if len(os.sys.argv) > 3:
                for arg in os.sys.argv[3:]:
                    cmd, ent = arg.split('=')
                    if cmd == 'aid':
                        aid = int(ent)
                    elif cmd == 'sid':
                        sid = int(ent)
                    elif cmd == 'title' or cmd == 'tit':
                        title = int(ent)
                    elif cmd == 'chapter' or cmd == 'chap':
                        chapter = int(ent)
            return run_extracting(title, chapter, name, aid, sid, donav)
        elif os.sys.argv[1][0:4] == 'file' and len(os.sys.argv) > 2:
            conffile = open(os.sys.argv[2], 'r')
            for line in conffile:
                items = line.split()
                if len(items) == 0:
                    continue
                name = items[0]
                title = int(items[1])
                if len(items) > 2:
                    for arg in items[2:]:
                        if len(arg.split('=')) > 1:
                            cmd, ent = arg.split('=')
                            if cmd == 'aid':
                                aid = int(ent)
                            elif cmd == 'sid':
                                sid = int(ent)
                            elif cmd == 'title' or cmd == 'tit':
                                title = int(ent)
                            elif cmd == 'chapter' or cmd == 'chap':
                                chapter = int(ent)
                run_extracting(title, chapter, name, aid, sid, donav)
        elif os.sys.argv[1] == 'rm' and len(os.sys.argv) > 2:
            name = os.sys.argv[2]
            run_command('rm %s/*/%s*' % (DIR, name))
            return 0
        elif os.sys.argv[1] == 'read':
            read_dvd()
            return 0
        else:
            return 0
    else:
        return 0
