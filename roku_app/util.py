#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
    Utility functions
'''

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import time
import socket
from contextlib import contextmanager
from subprocess import call, Popen, PIPE

HOMEDIR = os.getenv('HOME')


class PopenWrapperClass(object):
    """ context wrapper around subprocess.Popen """
    def __init__(self, command):
        """ init fn """
        self.command = command
        self.pop_ = Popen(self.command, shell=True, stdout=PIPE)

    def __iter__(self):
        return self.pop_.stdout

    def __enter__(self):
        """ enter fn """
        return self.pop_.stdout

    def __exit__(self, exc_type, exc_value, traceback):
        """ exit fn """
        if hasattr(self.pop_, '__exit__'):
            efunc = getattr(self.pop_, '__exit__')
            return efunc(exc_type, exc_value, traceback)
        else:
            self.pop_.wait()
            if exc_type or exc_value or traceback:
                return False
            else:
                return True


def run_command(command, do_popen=False, turn_on_commands=True,
                single_line=False):
    """ wrapper around os.system """
    if not turn_on_commands:
        print(command)
        return command
    elif do_popen:
        if single_line:
            with PopenWrapperClass(command) as pop_:
                return pop_.read()
        else:
            return PopenWrapperClass(command)
    else:
        return call(command, shell=True)


def test_run_command():
    """ test run_command """
    cmd = 'echo "HELLO"'
    out = run_command(cmd, do_popen=True, single_line=True).strip()
    assert out == b'HELLO'

    out = run_command(cmd, turn_on_commands=False)
    assert out == cmd


def send_command(ostr, host='localhost', portno=10888, socketfile=None):
    ''' send string to specified socket '''
    net_type = socket.AF_INET
    stm_type = socket.SOCK_STREAM
    addr_obj = (host, portno)
    if socketfile:
        net_type = socket.AF_UNIX
        addr_obj = socketfile

    retval = ''
    sock_ = socket.socket(net_type, stm_type)
    try:
        sock_.connect(addr_obj)
    except Exception as exc:
        print('failed to open socket %s' % exc)
        return False

    sock_.send(b'%s\n' % ostr)
    retval = sock_.recv(1024)
    sock_.close()
    return retval


def convert_date(input_date):
    ''' convert date string MM-DD-YY to date object '''
    import datetime
    _month = int(input_date[0:2])
    _day = int(input_date[2:4])
    _year = 2000 + int(input_date[4:6])
    return datetime.date(_year, _month, _day)


def print_h_m_s(second):
    ''' convert time from seconds to hh:mm:ss format '''
    hours = int(second / 3600)
    minutes = int(second / 60) - hours * 60
    seconds = int(second) - minutes * 60 - hours * 3600
    return '%02i:%02i:%02i' % (hours, minutes, seconds)


def print_m_s(second):
    ''' convert time from seconds to mm:ss format '''
    hours = int(second / 3600)
    minutes = int(second / 60) - hours * 60
    seconds = int(second) - minutes * 60 - hours * 3600
    if hours == 0:
        return '%02i:%02i' % (minutes, seconds)
    else:
        return '%02i:%02i:%02i' % (hours, minutes, seconds)


def datetimestring(date_):
    ''' input should be datetime object, output is string '''
    if not hasattr(date_, 'strftime'):
        return date_
    str_ = date_.strftime('%Y-%m-%dT%H:%M:%S%z')
    if len(str_) == 24 or len(str_) == 20:
        return str_
    elif len(str_) == 19 and 'Z' not in str_:
        return '%sZ' % str_


def datetimefromstring(tstr, ignore_tz=False):
    ''' parse datetime string '''
    import dateutil.parser
    return dateutil.parser.parse(tstr, ignoretz=ignore_tz)


class OpenUnixSocketServer(object):
    ''' wrapper around server socket for context manager '''
    def __init__(self, socketfile):
        self.sock = None
        self.socketfile = socketfile
        if os.path.exists(socketfile):
            os.remove(socketfile)
        return

    def __enter__(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            self.sock.bind(self.socketfile)
            os.chmod(self.socketfile, 0o777)
        except Exception as exc:
            time.sleep(10)
            print('failed to open socket %s' % exc)
            return self.__enter__()
        self.sock.listen(0)
        return self.sock

    def __exit__(self, exc_type, exc_value, traceback):
        if self.sock:
            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
        if exc_type or exc_value or traceback:
            return False
        else:
            return True


class OpenSocketConnection(object):
    ''' wrapper around socket.accept for context manager '''
    def __init__(self, sock):
        self.sock = sock
        self.conn = None

    def __enter__(self):
        self.conn, _ = self.sock.accept()
        return self.conn

    def __exit__(self, exc_type, exc_value, traceback):
        if self.conn:
            self.conn.close()
        if exc_type or exc_value or traceback:
            return False
        else:
            return True


def test_popenwrapper():
    """ test PopenWrapperClass """
    cmd_ = 'echo "HELLO"'
    output_ = None
    with PopenWrapperClass(cmd_) as pop_:
        output_ = pop_.read().strip().decode()
    assert output_ == 'HELLO'


def test_convert_date():
    """ test convert_date """
    import datetime
    inp_date = '111780'
    out_date = convert_date(inp_date)
    if out_date.year > datetime.date.today().year:
        out_date = datetime.date(year=out_date.year-100,
                                 month=out_date.month,
                                 day=out_date.day)
    assert out_date == datetime.date(1980, 11, 17)
