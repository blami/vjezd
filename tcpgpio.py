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

""" TCPGPIO protocol and server.

    TCPGPIO protocol is simple insecure TCP/IP protocol for remotely controling
    GPIO pins of Raspberry Pi and also server for this protocol.
"""

import sys
import os
import getopt
import socket
import select
import signal
import time
import logging
logger = logging.getLogger(__name__)


# Python version check
v = sys.version_info
if v[0] < 3 or (v[0] == 3 and v[:2] < (3,3)):
    raise ImportError('Application requires Python 3.3 or above')
del v

# Release information
# FIXME perhaps load from generated file (e.g. from git tags)
__author__ = 'Ondrej Balaz'
__license__ = 'BSD'
__version__ = '1.0'


# Protocol

class TCPGPIOInvalidMessageError(Exception):
    """ Exception raised when serialized message is invalid.
    """
    pass


class TCPGPIOMessage(object):
    """ TCPGPIOMessage implements simple insecure protocol for controling GPIO
        pins of Raspberry Pi remotely.

        Message has a following format (as sent over network):

        .. code-block:: python
            devid:type:pin:value

        Notes:
        * ``REPLY`` message to ``WRITE`` and ``PING`` requests always uses
          ``NONE`` as value.
        * ``REPLY`` message to ``READ`` uses read state as a value, except in
          case the read operation was unsuccessful. In that case ``NONE`` is
          used and client should handle it.
        * ``XWRITE`` message means an exclusive write which will lock the pin
          until next write operation from same device on same pin and opposite
          value is done (which literally unlocks pin). Until pin is locked no
          replies are sent nor values written to other devices.

        NOTE: for GPIO pin numbering we always use board numbering, not BCM
        mapping.
    """

    # Message type constants
    WRITE = 0
    XWRITE = 4
    REPLY = 2

    # Message pin value constants
    LOW = 0
    HIGH = 1
    NONE = 2


    def __init__(self, *args):
        """ Initialize the message.

            Depending on use case (and protocol side) object can be initialized
            in the following ways:
            .. code-block:: python

                msg = TCPGPIOMessage(devid, type, pin, value) # on sending side
                msg = TCPGPIOMessage(bytes) # on receiving side

            NOTE: parameters are positional.

            :param msg string:      message serialized to string
            :param devid string:    device identifier
            :param type integer:    message type
            :param pin integer:     pin number
            :param value integer:   pin value, defaults to NONE
        """

        if len(args) >= 3:
            # Initialize new message
            self.devid = args[0]
            self.type = args[1]
            self.pin = args[2]
            self.value = args[3] if len(args) == 4 else self.NONE

        elif len(args) == 1:
            # Deserialize string back to message
            parts = args[0].split(':')
            if len(parts) != 4:
                raise TCPGPIOInvalidMessageError('Invalid message')

            self.devid = parts[0]
            self.type = int(parts[1])
            self.pin = int(parts[2])
            self.value = int(parts[3])

        else:
            # Invalid message
            raise TypeError('Invalid set of arguments')


    def __repr__(self):
        """ Represent message as string as communicated over network.
        """
        return '{}:{}:{}:{}'.format(
            self.devid, self._type, self._pin, self._value)


    @property
    def type(self):
        """ Get message type.
        """
        return self._type


    @type.setter
    def type(self, v):
        """ Set message type.
        """
        if v not in (self.WRITE, self.XWRITE, self.REPLY):
            raise ValueError('Invalid message type')
        self._type = v


    @property
    def pin(self):
        return self._pin


    @pin.setter
    def pin(self, v):
        """ Set pin number.
        """
        if v not in (3, 5, 7, 8, 10, 11, 12, 13, 15, 16, 18, 19, 21, 22,
            23, 24, 26):
            raise ValueError('Invalid GPIO pin number')
        self._pin = v


    @property
    def value(self):
        """ Get pin value.
        """
        if self._value == self.NONE:
            return None
        return self._value


    @value.setter
    def value(self, v):
        """ Set message value.
        """
        if v not in (self.LOW, self.HIGH, self.NONE):
            raise ValueError('Invalid GPIO pin value')
        self._value = v


# Server

# Constants
# Application name
APP_NAME = os.path.basename(os.path.splitext(sys.argv[0])[0])
# Application version
APP_VER = __version__

# Globals
_server = None
_exiting = False

# Dictionary where pin is key to tuple of locking device and locking value
_pin_locks = {}


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
    if _server:
        logger.debug('Closing socket')
        _server.close()


def gpio_write(pin, value):
    """ Process GPIO message.

        :param pin integer:         GPIO pin number
        :param value integer:       GPIO pin value to be written (use
                                    TCPGPIOMessage constants except NONE)
    """
    if pin not in (3, 5, 7, 8, 10, 11, 12, 13, 15, 16, 18, 19, 21, 22,
        23, 24, 26):
        logger.error('Invalid GPIO pin {}!'.format(pin))
        return

    if value not in (TCPGPIOMessage.LOW, TCPGPIOMessage.HIGH):
        logger.error('Invalid GPIO pin value {}!'.format(value))
        return

    if has_gpio:
        gpio_value = GPIO.LOW
        if value == TCPGPIOMessage.HIGH:
            gpio_value = GPIO.HIGH
        # Set level on given GPIO pin
        gpio.output(pin, gpio_value)

    logger.info('GPIO pin {} set to value {}'.format(pin, value))


# Application entry point
if __name__ == '__main__':

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

    # Improve debugging by allowing application to just emulate GPIO on non
    # Raspberry Pi systems.
    has_gpio = True
    try:
        import RPi.GPIO as GPIO
    except RuntimeError as err:
        logger.error('{}'.format(err))
        if opt_loglevel == logging.DEBUG:
            has_gpio = False
        else:
            print('error: to run without GPIO use --debug argument')
            sys.exit(1)

    # Setup signal handler
    # TODO

    # Configure GPIO pin numbering
    if has_gpio:
        GPIO.setup(GPIO.BOARD)

    # Configure TCP/IP server socket
    logger.debug('Opening socket')
    _server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    _server.setblocking(0)
    _server.bind((opt_ip, opt_port))

    # Listen for an incoming connections
    logger.info('Listening on {}:{}...'.format(opt_ip, opt_port))
    _server.listen(0)

    inputs = [_server]
    outputs = []

    while not _exiting:
        try:
            r, w, x = select.select(inputs, outputs, [], 1)

            for s in r:
                # Handle incomming connections
                if s == _server:
                    client, ip = _server.accept()
                    logger.info('Client connection {}'.format(ip))
                    inputs.append(client)
                    outputs.append(client)

                # Handle client requests
                else:
                    d = s.recv(1024).decode('utf-8')

                    # Received message from client
                    if d:
                        try:
                            msg = TCPGPIOMessage(d)
                            locked = False

                            # Handle message
                            # Write
                            if msg.type == TCPGPIOMessage.WRITE:
                                gpio_write(msg.pin, msg.value)

                            # Exclusive write
                            elif msg.type == TCPGPIOMessage.XWRITE:
                                # Check whether locked or not
                                lock = _pin_locks.get(msg.pin)
                                if lock:
                                    locked = True

                                if not locked:
                                    logger.debug('{} locks pin {}'.format(
                                        msg.devid, msg.pin))
                                    _pin_locks[msg.pin] = (msg.devid, msg.value)

                                    # Write to locked pin
                                    gpio_write(msg.pin, msg.value)
                                    # DON'T SET locked=True HERE AS WE WANT TO
                                    # SEND REPLY!

                                # Locked here implies we have lock
                                elif locked and (
                                        msg.value == TCPGPIOMessage.LOW and \
                                        lock[1] == TCPGPIOMessage.HIGH \
                                    ) or ( \
                                        msg.value == TCPGPIOMessage.HIGH and \
                                        lock[1] == TCPGPIOMessage.LOW \
                                    ):

                                    logger.debug('{} unlocks pin {}'.format(
                                        msg.devid, msg.pin))
                                    # Write to pin
                                    gpio_write(msg.pin, msg.value)

                                    del _pin_locks[msg.pin]
                                    locked = False

                            print(_pin_locks)

                            # Send reply (if not locked and if required)
                            if not locked:
                                logger.debug('Sending REPLY')
                                # reply devid is same as sender, pin is same
                                # too (not used anyway), value is NONE
                                reply = TCPGPIOMessage(msg.devid,
                                    TCPGPIOMessage.REPLY, msg.pin,
                                    TCPGPIOMessage.NONE)
                                s.send(repr(reply).encode('utf-8'))

                        except TCPGPIOInvalidMessageError as err:
                            logger.error('Invalid message {}'.format(d))
                    # Client hung up
                    else:
                       logger.info('Client disconnect {}'.format(
                           s.getsockname()[0]))
                       inputs.remove(s)
                       outputs.remove(s)
                       s.close()

        except Exception as err:
            logger.critical('Error: {}'.format(err))
            finalize()
            sys.exit(1)

    finalize()
    sys.exit()
