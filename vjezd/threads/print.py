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

""" Print Thread
    ============

    Print thread is supposed to operate device in print mode. Basic workflow of
    this thread is to:

    * wait for button press
    * print ticket
    * switch relay

"""

import logging
logger = logging.getLogger(__name__)

#from sqlalchemy.exc import SQLAlchemyError

from vjezd import db
from vjezd.models import Ticket
from vjezd.threads.base import BaseThread
from vjezd.ports import port, PortWriteError


class PrintThread(BaseThread):
    """ Print thread class.
    """

    def do(self):
        """ Poll for button press and once pressed print a ticket.
        """
        port('button').read(callback=self.button_callback)


    def button_callback(self, data=None):
        """ Callback function for button port read event.

            Once the button is pressed following actions are done:
            #. Check opening hours
            #. If open, generate new ticket and print it
            #. Once printed activate relay in print mode
            #. Flush button port to ignore queued events (while relay open)
        """
        logger.info('Button pressed')

        # Check hours
        if not self.check_hours():
            logger.warning('Event past opening hours. Ignoring')

            db.session.remove()
            return

        # Create new ticket
        ticket = Ticket()
        db.session.add(ticket)

        try:
            port('printer').write(ticket)
            port('relay').write('print')
        except PortWriteError as err:
            # In case port write raised an exception rollback the session
            logger.error('Cannot write port {}!'.format(err))

            db.session.remove()
            return

        # Commit DB transaction once ticket is successfuly issued
        db.session.commit()
        db.session.remove()

        # Ignore all events queued during the relay period
        port('button').flush()
