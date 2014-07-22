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

""" Raspberry Pi GPIO Registry
    ==========================

    Due to poor design of RPi.GPIO library it is complicated to drive multiple
    GPIO ports (as in vjezd application ports). This helper provides set of
    threadsafe functions that ensure the RPi.GPIO is properly initialized when
    first GPIO port is opened and properly cleaned up when last GPIO port is
    closed.
"""

import threading
import logging
logger = logging.getLogger(__name__)

import RPi.GPIO as GPIO

from vjezd.ports.base import BasePort

_registry = []
_lock = threading.Lock()


def register(port):
    """ Register new GPIO port.

        If port registry is empty do all the initialization.

        :param port BasePort:       instance of port to be registered
    """
    if not isinstance(port, BasePort):
        raise TypeError('Object is not BasePort class descendant')

    logger.debug('Waiting for GPIO lock')
    with _lock:
        # Check port pin is still free
        #for r in _registry:
        #    if r.pin = port.pin:
        #        raise 

        # If required initialize GPIO
        if not _registry:
            logger.debug('GPIO not initialized. Initializing')
            GPIO.setmode(GPIO.BOARD)

        # Append port to registry
        logger.debug('GPIO registered port {} pin={}'.format(
            type(port).__name__, port.pin))
        _registry.append(port)


def unregister(port):
    """ Unregister registered GPIO port.

        If port registry gets empty after unregistering do a cleanup.

        :param port BasePort:       instance of port to be unregisterd
    """
    if not isinstance(port, BasePort):
        raise TypeError('Object is not BasePort class descendant')

    logger.debug('Waiting for GPIO lock')
    with _lock:
        # If port is not in registry, output warning and just continue as
        # following code isn't harmful
        if port not in _registry:
            logger.warning('Port is not registered!')
        else:
            _registry.remove(port)

        # If port registry is empty do a cleanup
        logger.debug('No GPIO ports. Cleaning up')
        GPIO.cleanup()
