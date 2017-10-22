#!/usr/bin/python
'''
    Script to record from roku device via WinTV HVR-1950
'''
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import re
from roku_app.remcom import make_transcode_script
from roku_app.roku_utils import publish_transcode_job_to_queue

if __name__ == '__main__':
    fnames = []
    do_add = False
    for arg in os.sys.argv:
        if 'transcode_avi' in arg:
            continue
        elif os.path.exists(os.path.abspath(arg)):
            fnames.append(os.path.abspath(arg))
        elif os.path.exists('%s/Documents/movies/%s' % (os.getenv('HOME'), arg)):
            fnames.append('%s/Documents/movies/%s' % (os.getenv('HOME'), arg))
        elif arg == 'add':
            do_add = True
    if not fnames:
        print('python transcode_avi.py <file>')
        exit(0)

    suffixes = ('avi', 'mp4', 'mkv')

    for fname in fnames:
        show = fname.split('/')[-1]
        bname = show
        oname = fname
        for suf in suffixes:
            show = re.sub('\.%s$' % suf, '', show)
            oname = re.sub('\.%s$' % suf, '', oname)

        tfile = make_transcode_script(fname)
        with open(tfile, 'a') as outf:
            outf.write('\n')
            outf.write('cp ~/Documents/movies/%s.mp4 %s.mp4.new\n' % (show, oname))
            outf.write('mv %s ~/Documents/movies/%s.old\n' % (fname, bname))
            outf.write('mv ~/Documents/movies/%s.old ~/Documents/movies/%s\n' % (bname, bname))
            outf.write('mv %s.mp4.new %s.mp4\n' % (oname, oname))
            if do_add:
                outf.write('/home/ddboline/bin/make_queue rm %s\n' % fname)
                outf.write('/home/ddboline/bin/make_queue add %s.mp4\n' % oname)
        publish_transcode_job_to_queue(tfile)
