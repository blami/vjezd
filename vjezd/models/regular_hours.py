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


""" Regular Hours Table
    ===================
"""

from datetime import datetime
import logging
logger = logging.getLogger(__name__)

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import CheckConstraint
from sqlalchemy import Integer, String, Time
from sqlalchemy import or_

from vjezd.db import Base


class RegularHours(Base):
    """ **Regular_hours** table contains regular opening hour rules. Devices
        will work in time intervals defined by rules in this table.

        .. note:: if there's overlap in rules the highest identifier (newest
            rule) wins.

        **Columns:**

        :ivar int id:               regular opening hours rule identifier
        :ivar str device:           device on which the rule applies, None for
                                    any device
        :ivar int day_of_week:      day of week when rule applies:
                                    0..6-week days (from Mon to Sun),
                                    7-work days
                                    8-all days
        :ivar Time time_start:      time of interval start
        :ivar Time time_end:        time of interval end
    """

    __tablename__ = 'regular_hours'
    __table_args__ = (
        CheckConstraint('0 <= day_of_week <= 8', name='cc_day_of_week'),
        CheckConstraint('time_end > time_start', name='cc_time'),
        {'extend_existing': True})

    id          = Column(Integer(), primary_key=True)
    device      = Column(String(16), ForeignKey('devices.id'), nullable=True)
    day_of_week = Column(Integer(), nullable=False)
    time_start  = Column(Time())
    time_end    = Column(Time())


    def __init__(self, day_of_week, time_start, time_end, device=None):
        """ Initialize new regular opening hours rule.
        """
        self.day_of_week = day_of_week
        self.time_start = time_start
        self.time_end = time_end
        self.device = device


    @staticmethod
    def check():
        """ Check whether currently are regular hours and device should act.

            :return:                True if at least one matching rule was
                                    found otherwise False
        """
        from vjezd import device as this_device

        t = datetime.now()

        # Setup list of valid day of week criteria vector
        d = [8]
        d.append(t.weekday())
        if t.weekday() < 5:
            d.append(7)

        # Find at least one matching rule
        regular_hours = RegularHours.query.filter(
            # only rules valid for this device
            or_(RegularHours.device == this_device.id,
                RegularHours.device == None),
            # AND meeting the day_of_week criteria
            RegularHours.day_of_week.in_(d),
            # AND meeting the time_start <= now <= time_end criteria
            RegularHours.time_start <= t.strftime('%H:%M:%S'),
            RegularHours.time_end >= t.strftime('%H:%M:%S')
            ).first()

        if regular_hours:
            return True

        return False
