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


""" Ticket Model
    ============
"""

import uuid
from datetime import datetime, timedelta
import logging
logger = logging.getLogger(__name__)

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer, String, Interval, DateTime

from vjezd.db import Base


class Ticket(Base):
    """ Ticket.
    """

    __tablename__ = 'tickets'
    __table_args__ = (
        {'extend_existing': True})

    id          = Column(Integer(), primary_key=True)
    code        = Column(String(240), nullable=False, unique=True)
    created     = Column(DateTime(), nullable=False, default=datetime.now())
    created_device = Column(String(16), ForeignKey('devices.id'),
                        nullable=False)
    used        = Column(DateTime())
    used_device = Column(String(16), ForeignKey('devices.id'))
    validity    = Column(Interval(), nullable=False, default='02:00:00')
    cancelled   = Column(DateTime())


    def __init__(self):
        """ Initialize new ticket with given validity period.
        """
        from vjezd.device import device as this_device
        from vjezd.models import Config

        # Generate the code
        self.code = Ticket.generate_code()

        self.created = datetime.now()
        self.created_device = this_device.id

        # Get validity (minutes) configuration option and convert it into time
        v = Config.get_int('validity')
        if v:
            self.validity = timedelta(minutes=v)


    def __repr__(self):
        """ String representation of object.
        """
        return '[Ticket {} validity:{} used:{}]'.format(
            self.code, self.validity, self.used)


    def expires(self):
        """ Calculate expiration time.
        """
        return self.created + self.validity


    @staticmethod
    def generate_code():
        """ Generate unique code based on timestamp and node part of UUID.
        """

        # Node is MAC address of interface, cut first three bytes which are
        # organization an probably same for all devices
        node = hex(int(uuid.uuid1().fields[5])).split('x')[1][6:]
        # NOTE This is naive but sufficient for current application
        ts = hex(int(datetime.now().strftime('%S%M%H%y%m%d'))).split('x')[1]

        # Final code, add separator
        code = '{}{}'.format(ts.upper(), node.upper())
        return code

