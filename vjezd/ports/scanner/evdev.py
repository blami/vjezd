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

""" Event Device Scanner
    ====================
"""

import os
import select
import logging
logger = logging.getLogger(__name__)

from evdev import InputDevice, ecodes as e, categorize
from evdev.events import KeyEvent

from vjezd.ports.base import BasePort


class EvdevScannerTestError(Exception):
    """ Exception raised when port test fails.
    """


class EvdevScanner(BasePort):
    """ Event scanner button port.

        Event device scanner port reads keyup events from the specified event
        device special file representing keyboard into a buffer. Once a RETURN
        key is read the buffer is flushed as a read code.

        Most barcode readers act as a HID keyboard. In order to make them work
        with this port they must be configured to send RETURN after code.

        Configuration
        -------------
        Port accepts the following positional arguments:
        #. /path/to/event_device - path to event device special file

        Full configuration line of evdev button is:
        ``scanner=evdev:/path/to/event_device``
    """

    # NOTE This is really incomplete but it works with ticket generator just
    # fine. Only missing symbols from Code39 (Standard) are %
    CODE39 = {
          2: '1',  3: '2',  4: '3',  5: ['4', '$'],    6: ['5', '%'],
          7: '6',  8: '7',  9: ['8', '*'],   10: '9', 11: '0', 12: '-',
         13: '+', 16: 'Q', 17: 'W', 18: 'E', 19: 'R', 20: 'T', 21: 'Y',
         22: 'U', 23: 'I', 24: 'O', 25: 'P', 30: 'A', 31: 'S', 32: 'D',
         33: 'F', 34: 'G', 35: 'H', 36: 'J', 37: 'K', 38: 'L', 44: 'Z',
         45: 'X', 46: 'C', 47: 'V', 48: 'B', 49: 'N', 50: 'M', 52: '.',
         53: '/', 57: ' ', }


    def __init__(self, *args):
        """ Initialize port configuration.
        """

        self.path = '/dev/input/event0'
        self.device = None

        if len(args) >= 1:
            self.path = args[0]

        self._buffer = ''
        self._shift = False
        self._caps = False

        logger.debug('Evdev scanner using: {}'.format(self.path))


    def test(self):
        """ Test if event device exists, is readable and has capability of
            reading a keypress.
        """
        if not os.access(self.path, os.R_OK | os.W_OK):
            raise EvdevScannerTestError('Cannot access {}'.format(self.path))

        # Check for EV_KEY capability
        inputdev = InputDevice(self.path)
        if 1 not in inputdev.capabilities():
            raise EvdevScannerTestError('Device has no EV_KEY capability')
        inputdev.close()


    def open(self):
        """ Open event device.
        """
        logger.debug('Opening evdev {}'.format(self.path))
        self.device = InputDevice(self.path)
        if self.device:
            logger.info('Evdev scanner found: {}'.format(self.device))


    def close(self):
        """ Close event device.
        """
        logger.debug('Closing evdev {}'.format(self.path))
        if self.is_open():
            self.device.close()


    def is_open(self):
        """ Check whether the event device is open.
        """
        if self.device:
            return True
        return False


    def read(self, callback=None):
        """ Read event device.

            If button event is triggered a function assigned to callback
            argument is run.
        """

        # In order to avoid bare polling a select() is called on device
        # descriptor with a reasonable timeout so the thread can be
        # interrupted. In case of event read we will read and process it.
        r, w, x = select.select([self.device.fileno()], [], [], 1)
        if r:
            event = self.device.read_one()
            if event.type == e.EV_KEY:
                data = categorize(event)

                skip = False
                # Handle shift
                if data.scancode in (e.KEY_LEFTSHIFT, e.KEY_RIGHTSHIFT):
                    if data.keystate == 1:
                        self._shift = True
                    elif data.keystate == 0:
                        self._shift = False
                    skip = True
                # Handle capslock
                if data.scancode == e.KEY_CAPSLOCK:
                    if data.keystate == 1:
                        self._caps = True
                    elif data.keystate == 0:
                        self._caps = False
                    skip = True

                # Read key up events, not capslock/shift
                if data.keystate == 0 and not skip:
                    if data.scancode != e.KEY_ENTER:
                        k = self.CODE39.get(data.scancode, '?')
                        if len(k) == 2:
                            if self._shift != self._caps:
                                k = k[1]
                            elif self._shift == self._caps:
                                k = k[0]
                        self._buffer += k
                    else:
                        logger.debug('Evdev buffer: {}'.format(self._buffer))
                        if callback and hasattr(callback, '__call__'):
                            callback(self._buffer)
                        self._buffer = ''


    def flush(self):
        """ Flush event device.
        """

        logger.debug('Flushing port')
        while True:
            r, w, x = select.select([self.device.fd], [], [], 0)
            if r:
                self.device.read_one()
            else:
                break



# Export port_class for port_factory()
port_class = EvdevScanner
