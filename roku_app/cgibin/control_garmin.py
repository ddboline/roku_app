#!/usr/bin/env python

# enable debugging
import cgi
import cgitb
cgitb.enable()
cgitb.enable(display=0, logdir='/tmp')

from control_roku import get_output

if __name__ == '__main__':

    form = cgi.FieldStorage()
    if "cmd" not in form:
        print "<H1>Error</H1>"
        print "Please fill in the cmd field."
    else:
        get_output(form['cmd'].value, socketfile='/tmp/.garmin_test_socket')
