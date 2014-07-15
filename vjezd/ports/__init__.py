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

""" Ports
    *****

    Ports are device I/O. Each device type has different needs and thus
    requires different ports. Currently application supports 4 different
    classes of ports (with modes which use it):

    * button: for trigger ticket printer button (print)
    * relay: for door opening relay (print, scan)
    * printer: for printing tickets (print)
    * scanner: for scanning tickets (scan)

    Each of these classes can have multiple implementations based on their
    base class. These implementations have to be thread-safe as in 'both' mode
    both printer and scanner might want access them.

    Configuration Options
    ---------------------
"""

import os
import importlib
import logging
logger = logging.getLogger(__name__)

from vjezd import conffile
from vjezd.ports.base import BasePort


# Port instances, if None, then device doesn't have this port
# NOTE Each port can have only single instance
button = None
relay = None
printer = None
scanner = None


def init():
    """ Initialize ports.
    """

    logger.debug('Initializing ports')

    button = port_factory('button')
    relay = port_factory('relay')
    printer = port_factory('printer')
    scanner = port_factory('scanner')

    logger.debug('Ports initialized')


def port_factory(port):
    """ Get port instance.

        Port class is imported from vjezd.ports.<port>.<port_class> and
        excepted to be assigned in port_class global variable.
    """
    logger.info('Trying to create port {}'.format(port))

    # Read the port configuration
    conf = conffile.get('ports', port, None)
    klass = None
    if conf:
        conf = conf.split(':')
        klass = conf[0]
        args = []
        if len(conf) > 1:
            args = conf[1].split(',')

    if not klass:
        logger.info('Port {} is not configured. Skipping.'.format(port))
        return None

    logger.info('Initializing port {} as class:{} with args:{}.'.format(
        port, klass, args))

    # Import and instantiate port class
    path = 'vjezd.ports.{}.{}'.format(port, klass)
    logger.debug('Importing port module from: {}'.format(path))

    inst = None
    try:
        module = importlib.import_module('{}'.format(path))
        obj = getattr(module, 'port_class')
        inst = obj(*args)
    except (ImportError, AttributeError) as err:
        logger.error('Cannot import port {} module: {}! Skipping'.format(
            port, err))
        return None

    # Instance must be of BasePort type
    if not isinstance(inst, BasePort):
        logger.error('Port {} class must inherit BasePort! Skipping.'.format(
            port))
        return None

    try:
        inst.test()
    except Exception as err:
        logger.error('Port {} test failed: {}!'.format(port, err))
        return None

    logger.info('Port {} created'.format(port))
    return inst
