#!/usr/bin/env python

# enable debugging
import cgi
import cgitb
cgitb.enable()
cgitb.enable(display=0, logdir='/tmp')

import socket

class OpenUnixSocketClient(object):
    def __init__(self, host='localhost', portno=10888,
                 socketfile='/tmp/.record_roku_socket'):
        self.sock = None
        self.socketfile = None
        self.host = host
        self.portno = portno
        if socketfile:
            self.socketfile = socketfile

    def __enter__(self):
        stm_type = socket.SOCK_STREAM
        if self.socketfile:
            net_type = socket.AF_UNIX
            addr_obj = self.socketfile
        else:
            net_type = socket.AF_INET
            addr_obj = (self.host, self.portno)
        self.sock = socket.socket(net_type, stm_type)
        try:
            err = self.sock.connect(addr_obj)
        except socket.error:
            return None
        if err:
            print(err)
        return self.sock

    def __exit__(self, exc_type, exc_value, traceback):
        self.sock.close()
        if exc_type or exc_value or traceback:
            return False
        else:
            return True


def send_command(ostr, host='localhost', portno=10888,
                 socketfile='/tmp/.record_roku_socket'):
    ''' send string to specified socket '''
    with OpenUnixSocketClient(host, portno, socketfile) as sock:
        if not sock:
            return 'Failed to open socket'
        sock.send(b'%s\n' % ostr)
        return sock.recv(1024)

def get_output(val, host='localhost', portno=10888,
               socketfile='/tmp/.record_roku_socket'):

    print "Content-Type: text/html\n\n\n"

    ostr = send_command(val, host, portno, socketfile)

    if ostr:
        print ostr.replace('command w','').replace('command','')

if __name__ == '__main__':

    form = cgi.FieldStorage()
    if "cmd" not in form:
        print "<H1>Error</H1>"
        print "Please fill in the cmd field."

    get_output(form['cmd'].value)
