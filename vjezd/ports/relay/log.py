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

""" Log Relay Port
    ==============
"""

import time
import logging
logger = logging.getLogger(__name__)

from vjezd.ports.relay.base import BaseRelay


class LogRelay(BaseRelay):
    """ Log relay.

        Log relay will just do INFO level log entry on event of write() when
        relay is switched ON and then also when it is switched OFF.

        Configuration
        -------------
        No positional arguments accepted.
    """

    def __init__(self, *args):
        logger.debug('Log relay initialized')


    def test(self):
        """ Log relay test always passes.
        """
        pass


    def write(self, data):
        """ Activate relay.

            :param data string:     activation mode (print or scan)
        """
        if data not in ('print', 'scan'):
            logger.error('Invalid activation mode: {}'.format(data))
            return

        # Get delay
        delay = self.get_delay(data)
        logger.info('Waiting configured delay {} seconds'.format(delay))
        time.sleep(delay)

        # Activate relay
        logger.info('Activating relay in {} mode'.format(data))


# Export port_class for port_factory()
port_class = LogRelay
