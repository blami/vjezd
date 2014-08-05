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

""" GPIO Relay
    ==========
"""

import time
import logging
logger = logging.getLogger(__name__)

import RPi.GPIO as GPIO

from vjezd.ports import gpio_registry
from vjezd.ports.relay.base import BaseRelay


class GPIORelayInvalidPinError(Exception):
    """ An exception raised when invalid GPIO pin number is configured.
    """


class GPIORelay(BaseRelay):
    """ Raspberry Pi GPIO relay port.

        Raspberry Pi GPIO pin driven 5V relay.

        Configuration
        -------------
        Port accepts the following positional arguments:
        #. pin - GPIO physical pin number (without P1_ prefix)

        Full configuration line of evdev button is:
        ``relay=gpio:pin``
    """

    def __init__(self, *args):
        self.pin = 18
        self._is_open = False

        if len(args) >= 1:
            self.pin = int(args[0])

        if self.pin not in (3, 5, 7, 8, 10, 11, 12, 13, 15, 16, 18, 19, 21, 22,
            23, 24, 26):
            raise GPIORelayInvalidPinError('Invalid GPIO pin {}'.format(
                self.pin))

        logger.info('GPIO relay using pin: {}'.format(self.pin))



    def test(self):
        """ Check if device is Raspberry Pi and GPIO is available.
        """
        pass


    def open(self):
        """ Open GPIO.
        """
        logger.info('Opening GPIO {}'.format(self.pin))
        gpio_registry.register(self)

        GPIO.setup(self.pin, GPIO.OUT)

        self._is_open = True


    def close(self):
        """ Close GPIO.
        """
        logger.info('Closing GPIO {}'.format(self.pin))
        if self._is_open:
            gpio_registry.unregister(self)
            self._is_open = False


    def is_open(self):
        """ Check whether the GPIO is open.
        """
        return self._is_open


    def activate(self, mode):
        """ Activate relay.

            :param data string:     activation mode (print or scan)
        """

        # Wait for configured delay or return in case the delay is < 0
        delay = self.get_delay(mode)
        if delay < 0:
            logger.warning('Delay set to < 0. Ommiting relay activation')
            return
        logger.info('Waiting configured delay {} seconds'.format(delay))
        time.sleep(delay)

        # Activate relay for configured period
        period = self.get_period(mode)
        logger.info('Activating relay in {} mode for {}s'.format(mode, period))

        GPIO.output(self.pin, GPIO.HIGH)
        time.sleep(period)
        GPIO.output(self.pin, GPIO.LOW)


# Export port_class for port_factory()
port_class = GPIORelay
