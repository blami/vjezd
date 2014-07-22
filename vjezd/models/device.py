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


""" Device Model
    ============
"""

from datetime import datetime
import logging
logger = logging.getLogger(__name__)

from sqlalchemy import Column
from sqlalchemy import Integer, String, DateTime, Enum

from vjezd import db
from vjezd.db import Base


class Device(Base):
    """ Named device acting in either printer, scanner or both modes.

        Device records in table *devices* are created for informative purposes
        and third party applications using same database. Each device is
        expected to create/update its own record once initialized.

        This table is considered to be read only. Any external changes will not
        be used in running instance (as it manages device internally) and will
        probably get overwriten during next startup.

        Fields
        ------
        :ivar id string:            device identifier read from configuration
        :ivar last__seen datetime:  timestamp of last update of record
        :ivar last_mode enum:       last mode in which was device operating
        :ivar last_ip string:       last IP address of device
    """

    __tablename__ = 'devices'
    __table_args__ = (
        {'extend_existing': True})


    id          = Column(String(8), primary_key=True)
    # TODO UUID can avoid situation where multiple devices have same id
    uuid        = Column(String(240), unique=True)
    last__seen  = Column(DateTime(), default=datetime.now())
    last_mode   = Column(Enum('print', 'scan', 'both'))
    last_ip     = Column(String(240))


    def __init__(self, id):
        """ Initialize object with given parameters.
        """
        self.id = id


    def __repr__(self):
        """ String representation of object.
        """
        return '[Device id:{} mode:{}]'.format(self.id, self.last_mode)


    @staticmethod
    def last_seen(id, mode, ip):
        """ Update last seen information about the device.
        """
        # NOTE Cannot use this_device stanza here because last_seen is called
        # just once from device initializer.

        # FIXME There should be mechanism that verifies device UUID at moment
        # we simply trust the setup there are no two devices configured with
        # same id.
        device = Device.query.filter(Device.id == id).first()

        if not device:
            # Create device record as it does not exist yet.
            logger.warning('Device {} DB record not found. Created'.format(id))
            device = Device(id)
            db.session.add(device)

        device.last_mode = mode
        device.last_ip = ip
        device.last__seen = datetime.now()
