#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Sun May 17 07:14:20 2015

@author: ddboline
"""
from __future__ import (absolute_import, division, print_function)
import sys
from setuptools import setup

console_scripts_ = (('run-recording', 'roku_app.record_roku:main'),
                   ('run-encoding',
                    'roku_app.run_encoding:run_encoding'), ('run-remcom-test',
                                                            'roku_app.remcom:remcom_test_main'),
                   ('run-remove-commercials',
                    'roku_app.remove_commercials:main'), ('play-roku',
                                                          'roku_app.roku_utils:play_roku'),
                   ('send-to-roku',
                    'roku_app.roku_utils:send_to_roku_main'), ('transcode-avi',
                                                               'roku_app.remcom:transcode_main'))

console_scripts = ['%s = %s' % (x, y) for x, y in console_scripts_]

v = sys.version_info.major
console_scripts.extend('%s%s = %s' % (x, v, y) for x, y in console_scripts_)

setup(
    name='roku_app',
    version='0.0.5.6',
    author='Daniel Boline',
    author_email='ddboline@gmail.com',
    description='roku_app',
    long_description='Roku Recording App',
    license='MIT',
    packages=['roku_app'],
    package_dir={'roku_app': 'roku_app'},
    package_data={'roku_app': [
        'roku_app/templates/*.html',
    ]},
    entry_points={
        'console_scripts': console_scripts
    })
