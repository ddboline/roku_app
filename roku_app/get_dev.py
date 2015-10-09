#!/usr/bin/python
''' get_dev module '''
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
try:
    from .util import run_command
except (ValueError, SystemError):
    from util import run_command


def is_module_loaded(user_mod='pvrusb2'):
    ''' has module been loaded? '''
    with run_command('lsmod', do_popen=True) as pop_:
        for line in pop_:
            if user_mod in line:
                return True
    return False


def get_dev(user_mod=''):
    '''
        use v4l-info to determine device for a given driver module
    '''
    if user_mod == 'bttv0':
        user_mod = 'bttv'

    with run_command('ls /dev/video*', do_popen=True) as pop_:
        for line in pop_:
            devname = line.strip()
            if hasattr(devname, 'decode'):
                devname = devname.decode()

            if not os.path.exists('/usr/bin/v4l-info'):
                print('YOU NEED TO INSTALL v4l-conf')
                exit(0)
            driver = ''
            with run_command('v4l-info %s 2> /dev/null | grep driver'
                             % devname, do_popen=True) as v4linfo:
                for line in v4linfo:
                    if hasattr(line, 'decode'):
                        line = line.decode()
                    if line != '':
                        driver = line.split()[2].strip('"')
                if user_mod in driver or (not user_mod and driver == 'em28xx'):
                    return devname


def test_is_module_loaded():
    """ test is_module_loaded """
    assert is_module_loaded() is True
    assert is_module_loaded('asdfasdf') is False


def test_get_dev():
    """ test get_dev """
    assert get_dev('pvrusb2') == '/dev/video0'


def main(args):
    """ main function """
    user_module = ''

    if len(args) > 1:
        user_module = args[1]

    return get_dev(user_module)


#def test_main():
#    """ test main """
#    assert main('pvrusb2') == '/dev/video0'

if __name__ == '__main__':
    print(main(os.sys.argv))
