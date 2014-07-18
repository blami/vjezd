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

""" FIFO (Named Pipe) Scanner
    =========================
"""

import os
import select
import logging
logger = logging.getLogger(__name__)

from vjezd.ports.base import BasePort


class FIFOScanner(BasePort):
    """ UNIX fifo (named pipe) scanner port.

        Reads on a configured UNIX fifo for incoming code in ASCII. Every time
        a code is submitted through UNIX fifo, scanner acts as if code was
        read. Codes are submitted in plain-text one line ('\\n') per code. If
        there's a non-line leftover before end of buffer, it's being ignored.

        UNIX fifo will be created on filesystem. If it already exists, program
        will fail.

        Configuration
        -------------
        Port accepts the following positional arguments:
        #. /path/to/fifo - filename of the scanner UNIX fifo

        Full configuration line is:
        ``scanner=fifo,/path/to/fifo``
    """

    def __init__(self, *args):
        """ Initialize port configuration.
        """

        self.fifo = None
        self.path = '/tmp/vjezd_scanner_fifo'
        if(len(args) > 0):
            self.path = args[0]

        logger.debug('Scanner is using UNIX fifo: {}'.format(self.path))


    def test(self):
        """ Test if configured UNIX fifo can be created/opened.
        """
        # FIXME
        pass


    def open(self):
        """ Create and open UNIX fifo.
        """
        logger.debug('Opening UNIX fifo: {}'.format(self.path))
        os.mkfifo(self.path)
        # Create fifo non-blocking (don't wait for other side)
        fd = os.open(self.path, os.O_RDONLY | os.O_NONBLOCK)
        self.fifo = os.fdopen(fd)


    def close(self):
        """ Close and destroy UNIX fifo.
        """
        logger.debug('Closing UNIX fifo: {}'.format(self.path))
        if self.is_open:
            self.fifo.close()
            logger.debug('Removing UNIX fifo filesystem object')
            os.remove(self.path)


    def is_open(self):
        """ Check whether the UNIX fifo is open.
        """
        if self.fifo:
            return True
        return False


    def read(self, callback=None):
        """ Read UNIX fifo.

            If code is detected a function assigned to callback argument is
            run.
        """
        # In order to avoid bare polling a select() is called on device
        # descriptor with a reasonable timeout so the thread can be
        # interrupted. In case of event read we will read and process it.
        r, w, x = select.select([self.fifo.fileno()], [], [], 1)
        if r:
            l = self.fifo.readline()
            self.fifo.flush()
            logger.debug('Read: {}'.format(l))


# Export port_class for port_factory()
port_class = FIFOScanner
