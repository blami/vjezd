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

from datetime import datetime, timedelta
import logging
logger = logging.getLogger(__name__)

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer, String, Time, DateTime

from vjezd import barcode
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
    validity    = Column(Time(), nullable=False, default='02:00:00')
    cancelled   = Column(DateTime())


    def __init__(self):
        """ Initialize new ticket with given validity period.
        """
        from vjezd.device import device as this_device
        from vjezd.models import Config

        # FIXME in barcode.py
        self.code = barcode.generate()

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
