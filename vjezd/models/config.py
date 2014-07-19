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


""" Config Model
    ============

    List of all supported configuration options:

    Option                      Description
    ==========================  ===============================================
    validity                    ticket validity (minutes)
    relay_print_delay           relay activation delay in print (seconds)
    relay_scan_delay            relay activation delay in scan (seconds)
    ticket_title                Title on ticket (e.g. device name)
    ==========================  ===============================================
"""

import logging
logger = logging.getLogger(__name__)

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint
from sqlalchemy import Integer, String
from sqlalchemy import or_

from vjezd.db import Base


class Config(Base):
    """ Global configuration option for one or more devices.

        Configuration option stored in the DB in *config* table is considered
        application-wide in opposite to option stored in device-local
        configuration file.

        Each option consists of ''option'' name, its ''value'' and optionally
        from a relation to ''device'' for which is option set.

        Theres a constraint on key ''option'', ''device'' but if device is NULL
        (which means that option is applicable for all devices) the unique does
        not take effect. In that case the option with highest identifier
        (latest one) has the highest priority and will be used.

        Please note that option names are case sensitive.

        Columns
        -------
        :ivar option string:        option name
        :ivar value string:         option value
        :ivar device string:        foreign key to the Device record for which
                                    is option set. If None, any device will
                                    match it.
    """

    __tablename__ = 'config'
    __table_args__ = (
        UniqueConstraint('option', 'device', name='uc_option_device'),
        {'extend_existing': True})

    id          = Column(Integer(), primary_key=True)
    option      = Column(String(100), nullable=False)
    value       = Column(String(240), nullable=True)
    device      = Column(String(16), ForeignKey('devices.id'), nullable=True)


    def __init__(self, option, value, device_id=None):
        """ Initialize configuration option with given parameters.
        """
        self.option = option
        self.value = value
        self.device_id = device_id


    def __repr__(self):
        """ String representation of object.
        """
        return '[Config {}={}, device:{}, id:{}]'.format(
            self.option, self.value, self.device, self.id)


    @staticmethod
    def get(option, fallback=None):
        """ Get option. If not found return fallback value.

            Option with device column set to current device id will be
            prioritized.

            :param fallback:        fallback value used in case the given
                                    option doesn't exists or its value is None
        """
        from vjezd.device import device as this_device

        o = Config.query.filter(
            # only rules valid for this device
            or_(Config.device == this_device.id,
                Config.device == None),
            # AND meeting the option name
            Config.option == option,
            ).order_by(Config.device.desc(), Config.id.desc()).first()

        if o:
            logger.debug('Read option from db: {}'.format(o))
            if o.value == None:
                return fallback
            return o.value

        return fallback


    @staticmethod
    def get_int(option, fallback=None):
        """ Get option and coerce it into integer if possible. Otherwise return
            fallback.
        """
        return int(Config.get(option, fallback))

