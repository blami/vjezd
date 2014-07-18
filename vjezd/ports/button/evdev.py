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

""" Test Button
    ===========
"""

import select
import logging
logger = logging.getLogger(__name__)

from evdev import InputDevice, ecodes
from evdev.events import KeyEvent

from vjezd.ports.base import BasePort


class EvdevButton(BasePort):
    """ Event device button port.

        Event device button port reads keypress events on specified event
        device special file.

        Configuration
        -------------
        Port accepts the following positional arguments:
        #. /path/to/event_device - path to event device special file
        #. scancode - scancode of trigger key

        Full configuration line of evdev button is:
        ``button=evdev,/path/to/event_device,keycode``
    """


    def __init__(self, *args):
        """ Initialize port configuration.
        """

        self.path = '/dev/input/event0'
        self.scancode = 57
        self.device = None

        if len(args) >= 1:
            self.path = args[0]
        if len(args) >= 2:
            self.scancode = int(args[1])

        logger.debug('Evdev button using: {} keycode={}'.format(
            self.path, self.scancode))


    def test(self):
        """ Test if event device exists, is readable and has capability of
            reading a keypress.
        """
        # FIXME
        pass


    def open(self):
        """ Open event device.
        """
        logger.debug('Opening evdev {}'.format(self.path))
        self.device = InputDevice(self.path)
        if self.device:
            logger.info('Evdev button found: {}'.format(self.device))


    def close(self):
        """ Close event device.
        """
        logger.debug('Closing evdev {}'.format(self.path))
        if self.is_open():
            self.device.close()


    def is_open(self):
        """ Check whether the device is open.
        """
        if self.device:
            return True
        return False


    def read(self, callback=None):
        """ Read port.

            If button event is triggered a function assigned to callback
            argument is run.
        """
        # In order to avoid bare polling a select() is called on device
        # descriptor with a reasonable timeout so the thread can be
        # interrupted. In case of event read we will read and process it.
        r, w, x = select.select([self.device.fd], [], [], 1)
        if r:
            e = self.device.read_one()
            if e.type == ecodes.EV_KEY \
                and e.value == 0 and e.code == self.scancode:
                    logger.debug('Trigger: {}'.format(e))
                    # Execute callback function
                    if callback and hasattr(callback, '__call__'):
                        callback()
                    return True
        return False


    def flush(self):
        """ Flush port.
        """

        logger.debug('Flushing port')
        while True:
            r, w, x = select.select([self.device.fd], [], [], 0)
            if r:
                self.device.read_one()
            else:
                break



# Export port_class for port_factory()
port_class = EvdevButton
