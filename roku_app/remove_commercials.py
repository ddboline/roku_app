#!/usr/bin/python
from __future__ import print_function

import os
from .util import run_command

HOMEDIR = os.getenv('HOME')
TMPDIR = '%s/tmp_avi' % HOMEDIR

def remove_commercials(INFILE='', OUTFILE='', TIMING_STRING='0,3600'):
    ''' cut and splice recorded file to remove undesired sections (commercials) '''
    from util import get_random_hex_string

    TEMPPRE = 'temp_%06x' % get_random_hex_string(3)

    def make_temp_avi(time, index):
        ''' convenience function, use mencoder to cut original file at specified begin/end times '''
        BEGIN = time[0]
        END = time[1]- time[0]
        DELAY = 0
        if len(time) > 2:
            DELAY = time[2]
        COMMAND = 'mencoder -mc 0 -idx %s -ovc copy -oac copy -ss %.1f -endpos %.1f -delay %.1f -o %s/%s_%03i.avi > %s/%s_%03i.out 2>&1' % (INFILE, BEGIN, END, DELAY, TMPDIR, TEMPPRE, index, TMPDIR, TEMPPRE, index)
        print(INFILE, BEGIN, time[1], END, DELAY, TMPDIR, index)
        #print(COMMAND)
        run_command(COMMAND)

    times = []
    for entry in TIMING_STRING.split():
        items = entry.split(',')
        if len(items) == 2:
            times.append([float(items[0]), float(items[1])])
        elif len(items) > 2:
            times.append([float(items[0]), float(items[1]), float(items[2])])

    run_command('mkdir -p %s' % TMPDIR)
    #run_command('rm %s/temp_*.avi %s/temp_*.out 2> /dev/null' % (TMPDIR, TMPDIR))
    run_command('chmod a-w %s' % INFILE)
    run_command('mv %s %s/backup_old.avi 2> /dev/null' % (OUTFILE, TMPDIR))

    if len(times) == 1:
        make_temp_avi(times[0], 0)
        run_command('mv %s/%s_000.avi %s' % (TMPDIR, TEMPPRE, OUTFILE))
    else:
        index = 0
        for time in times:
            make_temp_avi(time, index)
            index += 1
        COMMAND = 'mencoder -mc 0 -idx -ovc copy -oac copy %s/%s_*.avi -o %s > %s/%s.out 2>&1' % (TMPDIR, TEMPPRE, OUTFILE, TMPDIR, TEMPPRE)
        print(OUTFILE, TMPDIR)
        run_command(COMMAND)

    run_command('chmod u+w %s' % INFILE)
    run_command('du -sh %s %s' % (INFILE, OUTFILE))
    run_command('rm %s/%s_*.avi %s/%s_*.out 2> /dev/null' % (TMPDIR, TEMPPRE, TMPDIR, TEMPPRE))

if __name__ == '__main__':
    INFILE = os.sys.argv[1]
    OUTFILE = INFILE.split('/')[-1]
    if len(os.sys.argv) > 2:
        OUTFILE = os.sys.argv[2]
    if len(os.sys.argv) > 3:
        TIMING_FILENAME = os.sys.argv[3]
    TIMING_STRING = open(TIMING_FILENAME, 'r').read()


    remove_commercials(INFILE, OUTFILE, TIMING_STRING)
