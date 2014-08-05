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

""" Scan Thread
    ===========
"""

import logging
logger = logging.getLogger(__name__)

from vjezd import db
from vjezd.models import Ticket
from vjezd.threads.base import BaseThread
from vjezd.ports import port, PortWriteError


class ScanThread(BaseThread):
    """ A class representing print mode thread.
    """

    def do(self):
        """ Poll for read codes and once scanned valid code open gate.
        """
        port('scanner').read(callback=self.scanner_callback)


    def scanner_callback(self, data=None):
        """ Callback function for scanner port read event.

            Once the code is scanned the following actions are done:
            #. Check opening hours
            #. Check if code is valid
            #. If valid use it
            #. Activate relay in scan mode
            #. Flush scanner port to ignore queued events (while relay open)
        """
        logger.info('Code scanned: {}'.format(data))

        # Check hours
        if not self.check_hours():
            logger.warning('Event past opening hours. Ignoring')

            db.session.remove()
            return

        # Validate ticket
        ticket = Ticket.validate(data)
        if not ticket:
            # FIXME some signalization to user?
            logger.info('Invalid ticket. Ignoring')

            db.session.remove()
            return

        # If ticket is valid use ticket
        ticket.use()

        # Activate relay
        try:
            port('relay').write('scan')
        except PortWriteError as err:
            # In case port write raised an exception rollback the session
            logger.error('Cannot write port {}!'.format(err))
            db.session.remove()


        # Commit DB transaction once ticket is succesfully used
        db.session.commit()
        db.session.remove()

        # Ignore all events queued during the relay period
        # NOTE This avoids other tickets being used before the gate closes
        port('scanner').flush()
