#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import socket, time
from subprocess import call, Popen, PIPE

HOMEDIR = os.getenv('HOME')

class PopenWrapperClass(object):
    def __init__(self, command):
        self.command = command

    def __enter__(self):
        self.pop_ = Popen(self.command, shell=True, stdout=PIPE,
                          close_fds=True)
        return self.pop_.stdout

    def __exit__(self, exc_type, exc_value, traceback):
        if hasattr(self.pop_, '__exit__'):
            return self.pop_.__exit__(exc_type, exc_value, traceback)
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
        return PopenWrapperClass(command)
    elif single_line:
        with PopenWrapperClass(command) as pop_:
            return pop_.read()
    else:
        return call(command, shell=True)

def run_remote_command(command, is_remote=False, sshclient=None):
    ''' wrapper around os.system which also handles ssh calls '''
    if not is_remote:
        return run_command(command, do_popen=True)
    elif not sshclient:
        cmd = 'ssh %s \"%s\"' % (is_remote, command)
        print(cmd)
        return Popen(cmd, shell=True, stdout=PIPE,
                     close_fds=True).stdout.read()
    else:
        sshclient.sendline(command)
        sshclient.prompt()
        output = sshclient.before.decode()
        return output.split('\n')[1:-1]

def send_command(ostr, host='localhost', portno=10888, socketfile=None):
    ''' send string to specified socket '''
    import socket
    net_type = socket.AF_INET
    stm_type = socket.SOCK_STREAM
    addr_obj = (host, portno)
    if socketfile:
        net_type = socket.AF_UNIX
        addr_obj = socketfile

    retval = ''
    s = socket.socket(net_type, stm_type)
    try:
        s.connect(addr_obj)
    except Exception:
        print('failed to open socket')
        return False

    s.send('%s\n' % ostr)
    retval = s.recv(1024)
    s.close()
    return retval

def convert_date(input_date):
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

def datetimestring(d):
    ''' input should be datetime object, output is string '''
    if not hasattr(d, 'strftime'):
        return d
    s = d.strftime('%Y-%m-%dT%H:%M:%S%z')
    if len(s) == 24 or len(s) == 20:
        return s
    elif len(s) == 19 and 'Z' not in s:
        return '%sZ' % s

def datetimefromstring(tstr, ignore_tz=False):
    import dateutil.parser
    #tstr = tstr.replace('-05:00', '-0500').replace('-04:00', '-0400')
    #print(tstr)
    return dateutil.parser.parse(tstr, ignoretz=ignore_tz)


class OpenUnixSocketServer(object):
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
        except:
            time.sleep(10)
            print('failed to open socket')
            return self.__enter__()
        print('open socket')
        self.sock.listen(0)
        return self.sock

    def __exit__(self, exc_type, exc_value, traceback):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()
        if exc_type or exc_value or traceback:
            return False
        else:
            return True


class OpenSocketConnection(object):
    def __init__(self, sock):
        self.sock = sock

    def __enter__(self):
        self.conn, _ = self.sock.accept()
        return self.conn

    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.close()
        if exc_type or exc_value or traceback:
            return False
        else:
            return True
