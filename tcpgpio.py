#!/usr/bin/env python3
# encoding: utf-8

# Copyright (c) 2014, Ondrej Balaz. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the name of the original author nor the names of contributors
#   may be used to endorse or promote products derived from this software
#   without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

""" TCPGPIO server.
"""

import sys
import os
import getopt
import socket
import select
import signal
import logging
logger = logging.getLogger(__name__)


# Python version check
v = sys.version_info
if v[0] < 3 or (v[0] == 3 and v[:2] < (3,3)):
    raise ImportError('Application requires Python 3.3 or above')
del v

# If VENV_PATH is set and points to virtualenv directory, activate it
virtualenv = os.getenv('VIRTUALENV_PATH')
if virtualenv:
    print('info: running in virtualenv {}'.format(virtualenv))
    activate_file = '{}/bin/activate_this.py'.format(virtualenv)

    if not os.access(activate_file, os.R_OK):
        print('error: {}'.format(virtualenv),
            file=sys.stderr)
        sys.exit(1)
    else:
        # Python 3.x has no execfile()
        with open(activate_file, "r") as f:
            exec(f.read(), dict(__file__=activate_file))


has_gpio = True
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    has_gpio = False

# Release information
# FIXME perhaps load from generated file (e.g. from git tags)
__author__ = 'Ondrej Balaz'
__license__ = 'BSD'
__version__ = '1.0'

# Constants
# Application name
APP_NAME = os.path.basename(os.path.splitext(sys.argv[0])[0])
# Application version
APP_VER = __version__

# Globals
server = None
exiting = False


class TCPGPIOMessage(object):
    """
    """
    pass


def help():
    """ Show short help message.
    """

    print("""{appname} - control Raspberry Pi GPIO over TCP/IP
Usage: {appname} [options]

Available options:
(Mandatory arguments to long options are mandatory for short options too. Using
command line arguments overrides configuration file options.)
-i, --ip=HOST               listen address
-p, --port=PORT             listen port
-d, --debug                 print debugging info on console
-h, --help                  show this short help message and exit
-V, --version               show version information and exit

Report {appname} bugs to <support@blami.net>.
See COPYING for license information.""".format(
        appname=APP_NAME))


def version():
    """ Show version information.
    """

    print("""{appname} v{version}
Copyright (c) 2014 {author}. All rights reserved.
Licensed under the {license} license. See COPYING for more details.""".format(
        appname=APP_NAME,
        version=__version__,
        author=__author__,
        license=__license__))


def finalize():
    """ Exit cleanly.
    """
    if has_gpio:
        GPIO.cleanup()
    if server:
        logger.debug('Closing socket')
        server.close()


def gpio_command(pin, direction, value=None):
    """ Process GPIO command.
    """
    # TODO check valid pins

    if direction == 'OUT':
        # Setup GPIO direction to out
        if has_gpio:
           GPIO.setup(pin, GPIO.OUT)
        logger.debug('GPIO pin {} set to direction OUT'.format(pin))

        # Parse value
        if value == 'LOW':
            if has_gpio:
                gpio_value = GPIO.LOW
            else:
                gpio_value = 0
        elif value == 'HIGH':
            if has_gpio:
                gpio_value = GPIO.HIGH
            else:
                gpio_value = 1
        else:
            logger.error('Value {} not supported!'.format(value))
            return

        # Write GPIO
        logger.info('Write GPIO pin={} value={}'.format(pin, value))
        if has_gpio:
            GPIO.output(pin, gpio_value)
    else:
        logger.error('Direction {} not supported!'.format(direction))


# Application entry point
if __name__ == '__main__':

    opt_ip = '0.0.0.0'
    opt_port = 7777
    opt_loglevel = logging.INFO

    # Process command line arguments
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:],
            'i:p:dhV', [
                'ip=',
                'port=',
                'debug',
                'help',
                'version'])
    except getopt.GetoptError as err:
        print('error: {}'.format(err), file=sys.stderr)
        help()
        sys.exit(1)
    for opt, arg in opts:
        if opt in ('-i', '--ip'):
            opt_ip = arg
        elif opt in ('-p', '--port'):
            opt_port = int(arg)
        elif opt in ('-d', '--debug'):
            opt_loglevel = logging.DEBUG
        elif opt in ('-h', '--help'):
            help()
            sys.exit()
        elif opt in ('-V', '--version'):
            version()
            sys.exit()

    # Setup logging
    log_format='%(asctime)s %(levelname)s [%(name)s ' \
        '%(funcName)s():%(lineno)d] %(message)s'
    log_datefmt='%Y-%m-%d %H:%M:%S'
    logging.basicConfig(format=log_format, datefmt=log_datefmt,
        level=opt_loglevel)

    # Setup signal handler
    # TODO

    # Configure GPIO pin numbering
    if has_gpio:
        GPIO.setup(GPIO.BOARD)

    # Configure TCP/IP server socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.setblocking(0)
    server.bind((opt_ip, opt_port))
    logger.info('Listening on {}:{}...'.format(opt_ip, opt_port))
    server.listen(0)

    inputs = [server]
    outputs = []

    while not exiting:
        r, w, x = select.select(inputs, outputs, [], 1)

        for s in r:
            # Handle incomming connections
            if s == server:
                client, ip = server.accept()
                logger.info('Client connection {}'.format(ip))
                inputs.append(client)
                outputs.append(client)

            # Handle client requests
            else:
                data = s.recv(1024).decode('utf-8')
                if data:
                    msg = data.rstrip('\n').split(',')
                    if len(msg) == 3 \
                        and msg[1] in ('OUT') \
                        and msg[2] in ('HIGH', 'LOW'):
                        # Got a valid message, process GPIO
                        gpio_command(int(msg[0]), msg[1], msg[2])
                    else:
                        logger.error('Invalid message {}'.format(data))
                else:
                    # Client hung up
                    logger.info('Client disconnect {}'.format(
                        s.getsockname()[0]))
                    inputs.remove(s)
                    outputs.remove(s)
                    s.close()

