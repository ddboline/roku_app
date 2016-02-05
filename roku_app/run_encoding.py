#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import os
import json
import time
from subprocess import check_output, STDOUT, CalledProcessError
try:
    from roku_utils import open_transcode_channel
except ImportError:
    from .roku_utils import open_transcode_channel

TURN_ON_COMMANDS = True

HOMEDIR = os.getenv('HOME')


def main_loop(channel):
    mf, _, body = channel.basic_get(queue='transcode_work_queue', no_ack=True)
    if mf and body:
        result = json.loads(body)
        script = result['script']

        print(script)

        if os.path.exists(script):
            output = check_output(['sh', script], stderr=STDOUT)

            new_path = script.split('/')[-1]
            os.rename(script, '%s/tmp_avi/%s' % (HOMEDIR, new_path))


def run_encoding():
    chan = open_transcode_channel()
    while True:
        try:
            main_loop(chan)
        except CalledProcessError as exc:
            print(exc)
        time.sleep(1)
    return
