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

""" UNIX Socket Scanner
    ===================
"""

import os
import select
import socket
import logging
logger = logging.getLogger(__name__)

from vjezd.ports.base import BasePort


class SocketScanner(BasePort):
    """ UNIX socket scanner port.

        Reads on a configured UNIX socket for incoming code. Every time
        a code is submitted through UNIX socket, scanner acts as if code was
        read. Codes are submitted in plain-text one line ('\\n') per code.

        UNIX socket family is DGRAM and length of one datagram is 1024B.
        Code can be sent using following command:

        $ echo -n '1234' | nc -w1 -uU /tmp/vjezd_scanner.sock

        UNIX socket will be created during the port open and destroyed during
        the port close. If it exists before open program will try to use it.

        Suitable for development.

        Configuration
        -------------
        Port accepts the following positional arguments:
        #. /path/to/socket - filename of the scanner UNIX fifo

        Full configuration line is:
        ``scanner=socket:/path/to/socket``
    """

    def __init__(self, *args):
        """ Initialize port configuration.
        """

        self.socket = None
        self.path = '/tmp/vjezd_scanner.sock'
        if(len(args) > 0):
            self.path = args[0]

        logger.debug('Scanner is using UNIX socket: {}'.format(self.path))


    def test(self):
        """ Test if configured UNIX socket can be created/opened.
        """
        # FIXME
        pass


    def open(self):
        """ Open UNIX socket.
        """
        logger.info('Opening UNIX socket: {}'.format(self.path))

        # Open non-blocking socket and bind it to UNIX special file
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.socket.bind(self.path)
        self.socket.setblocking(0)


    def close(self):
        """ Close and destroy UNIX socket.
        """
        logger.info('Closing UNIX socket: {}'.format(self.path))
        if self.is_open:
            self.socket.close()
            self.socket = None
            logger.debug('Removing UNIX socket file: {}'.format(self.path))
            os.remove(self.path)


    def is_open(self):
        """ Check whether the UNIX socket is open.
        """
        if self.socket:
            return True
        return False


    def read(self, callback=None):
        """ Read UNIX socket.

            If code is detected a function assigned to callback argument is
            run.
        """
        # In order to avoid bare polling a select() is called on device
        # descriptor with a reasonable timeout so the thread can be
        # interrupted. In case of event read we will read and process it.
        r, w, x = select.select([self.socket], [], [], 1)
        if r:
            data = self.socket.recv(1024)
            if data:
                data = data.decode('ascii')
                logger.debug('Received data: {}'.format(data))
                if callback and hasattr(callback, '__call__'):
                    callback(data)


    def flush(self):
        """ Flush UNIX socket.
        """
        logger.debug('Flushing UNIX socket')
        while True:
            r, w, x = select.select([self.socket], [], [], 0)
            if r:
                self.socket.recv(1024)
            else:
                break


# Export port_class for port_factory()
port_class = SocketScanner
