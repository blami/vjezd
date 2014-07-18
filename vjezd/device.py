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

""" Device
    ******

    Device is configur

    Configuration Options
    ---------------------
"""

import socket
import logging
logger = logging.getLogger(__name__)

from sqlalchemy.exc import SQLAlchemyError

from vjezd import crit_exit
from vjezd import conffile
from vjezd import ports
from vjezd import db
from vjezd.models import Device


def init(id=None, mode=None):
    """ Initialize the device.
    """
    logger.debug('Initializing device')

    # Determine device identifier
    if not id:
        id = conffile.get('device', 'id')
    if not id:
        logger.critical('Device identifier must be set!')
        crit_exit(3)

    # Determine device mode. In case of misspeled or wrong
    if not mode:
        mode = conffile.get('device', 'mode', 'auto')
        if mode.lower() not in ('scan', 'print', 'both', 'auto'):
            logger.warning(
                'Unknown mode {}. Falling back to auto'.format(mode))
            mode='auto'

    # Dependency matrix for each mode.
    dep = {
        'both': ['button', 'relay', 'printer', 'scanner'],
        'print': ['button', 'relay', 'printer'],
        'scan': ['scanner', 'relay']}

    # If mode is auto, decide device mode based on ports.
    if mode == 'auto':
        logger.debug('Trying to auto-detect mode based on available ports')

        # Make dep dict doesn't guarantee order, sort by lenght of dep list.
        for d in sorted(dep.keys(), key=lambda k: len(dep[k]), reverse=True):
            if ports.has_ports(dep[d]):
                mode = d
                break

        if mode == 'auto':
            logger.critical('No suitable mode for device ports!')
            crit_exit(3)

        logger.info('Auto-detected mode: {}'.format(mode))

    # If mode is given (print, scan, both) just verify requirements and fail in
    # case they're not met.
    else:
        if not ports.has_ports(dep[mode]):
            logger.critical('Mode {} requires ports: {}; missing: {}'.format(
                mode, dep[mode], [p for p in dep[mode] if not ports.port(p)]))
            crit_exit(3)

        logger.info('Device mode: {}'.format(mode))

    # Get device model
    try:
        global device
        device = Device.query.filter(Device.id == id).first()

        # FIXME There should be mechanism that verifies device UUID at moment
        # we simply trust the setup there are no two devices configured with
        # same id.

        if not device:
            # Create device record as it does not exist yet.
            logger.warning('Device {} DB record does not exist'.format(id))
            device = Device(id)

            db.session.add(device)

        # Update device
        device.last_seen(mode, get_ip())

        # Commit changes
        db.session.commit()

    except SQLAlchemyError as err:
        logger.critical('Unable to get device object: {}!'.format(err))
        crit_exit(3, err)

    # Open the device ports
    ports.open_ports(dep[mode])

    logger.debug('Device {} initialized.'.format(id))


def finalize():
    """ Finalize device.
    """

    ports.close_ports()


def get_ip():
    """ Get device IP address.

        Please note that function uses socket.gethostbyname() so device
        hostname MUST NOT BE ASSIGNED TO 127.0.0.1 entry in /etc/hosts.
    """
    ip = socket.gethostbyname(socket.gethostname())

    logger.debug('Using IP address: {}'.format(ip))
    return ip


def get_uuid():
    """ Get an unique identifier of the system.
    """
    pass
