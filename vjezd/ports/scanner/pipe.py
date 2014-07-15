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

""" Pipe Scanner
    ============
"""

import logging
logger = logging.getLogger(__name__)

from vjezd.ports import BasePort


class PipeScanner(BasePort):
    """ UNIX pipe scanner port.

        Reads on a configured UNIX pipe for incoming code in ASCII. Every time
        a code is submitted through UNIX pipe, scanner acts as if code was
        read. Codes are submitted in plain-text one line per code.

        Configuration
        -------------
        Port accepts the following positional arguments:
        #. /path/to/pipe - filename of the scanner UNIX pipe

        Full configuration line is:
        ``scanner=pipe,/path/to/pipe``
    """

    def __init__(self, *args):
        """ Initialize port configuration.
        """

        self.pipe = '/tmp/vjezd_scanner_pipe'
        if(len(args) > 0):
            self.pipe = args[0]

        logger.debug('Scanner is using UNIX pipe: {}'.format(self.pipe))


    def test(self):
        """ Test if configured UNIX pipe can be created/opened.
        """
        # FIXME
        pass



# Export port_class for port_factory()
port_class = PipeScanner
