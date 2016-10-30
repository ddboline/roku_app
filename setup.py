#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Sun May 17 07:14:20 2015

@author: ddboline
"""
from __future__ import (absolute_import, division, print_function)

from setuptools import setup

setup(
    name='roku_app',
    version='0.0.3.8',
    author='Daniel Boline',
    author_email='ddboline@gmail.com',
    description='roku_app',
    long_description='Roku Recording App',
    license='MIT',
    packages=['roku_app'],
    package_dir={'roku_app': 'roku_app'},
    package_data={'roku_app': ['roku_app/templates/*.html', ]},
    entry_points={'console_scripts':
                  ['run-recording = roku_app.record_roku:main', 
                   'run-remcom-test = roku_app.remcom:remcom_test_main',
                   'run-remove-commercials = roku_app.remove_commercials:main',
                   'play-roku = roku_app.roku_utils:play_roku']}
)
