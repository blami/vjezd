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


""" Exception Hours Model
    =====================
"""

import logging
logger = logging.getLogger(__name__)

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import CheckConstraint
from sqlalchemy import Integer, String, Date, Time, Enum

from vjezd.db import Base


class ExceptionHours(Base):
    """ Exceptional opening hours. Devices will override their regular behavior
        according to rules in this table.

        If there's overlap in rules the highest identifier (newest rule) wins.

        :ivar id integer:           regular opening hours rule identifier
        :ivar device string:        device on which the rule applies, None for
                                    any device
        :ivar exception_date Date:  date of exception
        :ivar exception_type string:type of exception, can be 'open' or
                                    'closed'
        :ivar time_start Time:      time of interval start
        :ivar time_end Time:        time of interval end

    """

    __tablename__ = 'exception_hours'
    __tableargs__ = (
        {'extend_existing': True},
        CheckConstraint('time_end > time_start', name='cc_time'))

    id          = Column(Integer(), primary_key=True)
    device      = Column(String(16), ForeignKey('devices.id'), nullable=True)
    exception_date = Column(Date(), nullable=False)
    exception_type = Column(Enum('open','closed'), nullable=False)
    time_start  = Column(Time())
    time_end    = Column(Time())


