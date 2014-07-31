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

""" TCPGPIO Relay
    =============
"""

import time
import socket
import logging
logger = logging.getLogger(__name__)

from vjezd.ports.relay.base import BaseRelay

#from tcpgpio import TCPGPIOMessage


class TCPGPIORelayConfigError(Exception):
    """ An exception raised when port is misconfigured.
    """
    pass


class TCPGPIORelayInvalidPinError(Exception):
    """ An exception raised when invalid GPIO pin number is configured.
    """
    pass


class TCPGPIORelay(BaseRelay):
    """ Raspberry Pi GPIO relay port over TCP.

        This module sends a message to configured TCP socket.

        Configuration
        -------------
        Port accepts the following positional arguments:
        #. ip - TCP/IP address of device running TCPGPIO server
        #. port - TCP/IP port to send message to
        #. pin - number of GPIO pin on remote device

        Full configuration line of evdev button is:
        ``relay=tcpgpio:ip,port,pin``
    """

    def __init__(self, *args):
        """ Initialize TCPGPIO port.
        """

        if len(args) < 3:
            raise TCPGPIORelayConfigError('Missing configuration arguments')

        self.ip = args[0]
        self.port = int(args[1])
        self.pin = int(args[2])

        if self.pin not in (3, 5, 7, 8, 10, 11, 12, 13, 15, 16, 18, 19, 21, 22,
            23, 24, 26):
            raise TCPGPIORelayInvalidPinError('Invalid GPIO pin {}'.format(
                self.pin))
        logger.info('TCPGPIO relay using host: {}:{} pin={}'.format(
            self.ip, self.port, self.pin))


    def test(self):
        """ TCPGPIO test always passes.
        """
        pass


    def open(self):
        """ TCPGPIO port is opened every time when used.
        """
        pass


    def close(self):
        """ TCPGPIO port is closed every time when used.
        """
        pass


    def is_open(self):
        """ TCPGPIO signals it's always open as its close just does nothing.
        """
        return True


    def activate(self, mode):
        """ Activate relay.

            :param data string:     activation mode (print or scan)
        """

        # Wait for configured delay
        delay = self.get_delay(mode)
        logger.info('Waiting configured delay {} seconds'.format(delay))
        time.sleep(delay)

        # Activate relay for configured period
        period = self.get_period(mode)
        logger.info('Activating relay in {} mode for {}s'.format(mode, period))

        self.send('HIGH')
        time.sleep(period)
        self.send('LOW')


    def send(self, state):
        """ Send TCPGPIO message.
        """
        msg = '{},OUT,{}\n'.format(self.pin, state)

        try:
            # Connect to TCPGPIO server and send message
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((self.ip, self.port))
            logger.debug('Connected to server {}:{}'.format(self.ip,
               self.port))

            logger.debug('Sending message: {}'.format(msg))
            client.send(msg.encode('utf-8'))

            client.close()
            logger.debug('Disconnected')

        except socket.error as err:
            # Yield error but continue in operation
            logger.error('Error connecting to TCPGPIO: {}! Ignoring'.format(
                err))


# Export port_class for port_factory()
port_class = TCPGPIORelay