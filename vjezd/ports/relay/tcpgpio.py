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

from vjezd.ports import PortWriteError
from vjezd.ports.relay.base import BaseRelay

from tcpgpio import TCPGPIOMessage


# Constants
TIMEOUT = 5.0
BUFFER_SIZE = 1024


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

        # Wait for configured delay or return in case the delay is < 0
        delay = self.get_delay(mode)
        if delay < 0:
            logger.warning('Delay set to < 0. Ommiting relay activation')
            return
        logger.info('Waiting configured delay {} seconds'.format(delay))
        time.sleep(delay)

        # Activate relay for configured period
        period = self.get_period(mode)
        logger.info('Activating relay in {} mode for {}s'.format(mode, period))

        self._send_message(self.pin, 1)
        time.sleep(period)
        self._send_message(self.pin, 0)


    def _send_message(self, pin, state):
        """ Send TCPGPIO message to server and process reply or timeout.
        """
        from vjezd.device import id as device_id

        # Create message
        value = TCPGPIOMessage.NONE
        if state == 1:
            value = TCPGPIOMessage.HIGH
        elif state == 0:
            value = TCPGPIOMessage.LOW
        msg = TCPGPIOMessage(device_id, TCPGPIOMessage.XWRITE, pin, value)

        client = None
        try:
            # Connect to TCPGPIO server and send message
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(TIMEOUT)

            client.connect((self.ip, self.port))
            logger.debug('Connected to server {}:{}'.format(self.ip,
                self.port))

            # Send message
            logger.debug('Sending message: {}'.format(msg))
            client.send(repr(msg).encode('utf-8'))

            # Wait for confirmation reply, if not received a socket timeout
            # exception
            d = client.recv(BUFFER_SIZE)
            if d:
                reply = TCPGPIOMessage(d.decode('utf-8'))
                logger.debug('Received reply: {}'.format(reply))
            else:
                logger.error('Server hung-up!')

            client.close()
            logger.debug('Disconnected')

        except (socket.error, socket.timeout) as err:
            logger.error('TCPGPIO network problem: {}! Ignoring'.format(err))
            if client:
                client.close()
            # Raise port write error that should be handled by worker threads
            raise PortWriteError('{}'.format(err))


# Export port_class for port_factory()
port_class = TCPGPIORelay
