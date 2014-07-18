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

""" Log Printer Port
    ================
"""

import logging
logger = logging.getLogger(__name__)

from vjezd.models import Ticket
from vjezd.ports.base import BasePort


class LogPrinter(BasePort):
    """ Log printer.

        Log relay will just do INFO level log entry on event of printing a
        ticket. Ticket code and validity is logged.

        Configuration
        -------------
        No positional arguments accepted.
    """

    def __init__(self, *args):
        logger.debug('Log printer initialized')


    def test(self):
        """ Log printer test always passes.
        """
        pass


    def write(self, data):
        """ Write out data.

            :param data Ticket:         Ticket object to be printed
        """
        if isinstance(data, Ticket):
            logger.info('Printing ticket: {}'.format(data))
        else:
            logger.error('Obtained data is not ticket: {}'.format(data))


# Export port_class for port_factory()
port_class = LogPrinter
