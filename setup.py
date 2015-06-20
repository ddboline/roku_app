#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Sun May 17 07:14:20 2015

@author: ddboline
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
#from __future__ import unicode_literals

from distutils.core import setup

setup(
    name='roku_app',
    version='00.00.01',
    author='Daniel Boline',
    author_email='ddboline@gmail.com',
    description='roku_app',
    long_description='Roku Recording App',
    license='MIT',
#    install_requires=['pandas >= 0.13.0', 'numpy >= 1.8.0'],
    packages=['roku_app'],
    package_dir={'roku_app': 'roku_app'},
    package_data={'roku_app': ['roku_app/templates/*.html']},
    scripts=['garmin.py']
)
