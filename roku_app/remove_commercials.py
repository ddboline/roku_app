#!/usr/bin/python
''' remove commercials '''
from __future__ import print_function

import os
from subprocess import check_output, STDOUT, CalledProcessError
from .roku_utils import get_random_hex_string, publish_transcode_job_to_queue
from .util import run_command

HOMEDIR = os.getenv('HOME')
TMPDIR = '%s/television/tmp' % HOMEDIR


def remove_commercials(infile='', outfile='', timing_string='0,3600',
                       do_async=False):
    '''
        cut and splice recorded file to remove undesired sections (commercials)
    '''
    temp_pre = 'temp_%06x' % get_random_hex_string(3)

    def make_temp_avi(time, index):
        '''
            convenience function,
            use mencoder to cut original file at specified begin/end times
        '''
        begin = time[0]
        end = time[1] - time[0]
        delay = 0
        if len(time) > 2:
            delay = time[2]
        command = 'mencoder -mc 0 -idx %s -ovc copy -oac copy ' % infile + \
                  '-ss %.1f -endpos %.1f ' % (begin, end,) + \
                  '-delay %.1f ' % delay + \
                  '-o %s/%s_%03i.avi ' % (TMPDIR, temp_pre, index,) + \
                  '> %s/%s_%03i.out 2>&1' % (TMPDIR, temp_pre, index)
        print(infile, begin, time[1], end, delay, TMPDIR, index)
        #print(command)
        run_command(command)

    times = []
    for entry in timing_string.split():
        items = entry.split(',')
        if len(items) == 2:
            times.append([float(items[0]), float(items[1])])
        elif len(items) > 2:
            times.append([float(items[0]), float(items[1]), float(items[2])])

    outdir = os.path.dirname(outfile)
    print('dirname', outdir)
    run_command('mkdir -p %s' % TMPDIR)
    run_command('chmod a-w %s' % infile)
    run_command('mv %s %s/backup_old.avi 2> /dev/null' % (outfile, TMPDIR))

    tmp_script_fname = '%s/television/jobs/%s.sh' % (HOMEDIR, temp_pre)
    tmp_script = open(tmp_script_fname, 'w')

    if len(times) == 1:
        make_temp_avi(times[0], 0)
        tmp_script.write('#!/bin/bash\n')
        tmp_script.write('mkdir -p %s\n' % outdir)
        tmp_script.write('mv %s/%s_000.avi %s\n' % (TMPDIR, temp_pre, outfile))
    else:
        index = 0
        for time in times:
            make_temp_avi(time, index)
            index += 1
        command = 'mencoder -mc 0 -idx -ovc copy -oac copy ' + \
                  '%s/%s_*.avi ' % (TMPDIR, temp_pre) + \
                  '-o %s > %s/%s.out 2>&1' % (outfile, TMPDIR, temp_pre)
        print(outfile, TMPDIR)
        run_command(command)

    tmp_script.write('chmod u+w %s\n' % infile)
    tmp_script.write('du -sh %s %s\n' % (infile, outfile))
    tmp_script.write('rm %s/%s_*.avi %s/%s_*.out 2> /dev/null\n' % (TMPDIR,
                                                                    temp_pre,
                                                                    TMPDIR,
                                                                    temp_pre))
    tmp_script.close()
    if do_async:
        publish_transcode_job_to_queue(tmp_script_fname)
        return tmp_script_fname
    else:
        try:
            output = check_output(['sh', tmp_script_fname], stderr=STDOUT)
            print(output)
        except CalledProcessError as exc:
            print(exc)

        os.remove(tmp_script_fname)
        return None
