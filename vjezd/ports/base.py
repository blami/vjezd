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

""" Port Base Class
"""

import logging
logger = logging.getLogger(__name__)


class BasePort(object):
    """ BasePort is an abstract base class for ports.

        Each port implementation (no matter which class it is should implement
        these methods.
    """

    def __init__(self, *args):
        """ Initialize port with arguments.

            Implementation of initializer should just verify and store args to
            port instance. It should NEVER try to open port as it might not be
            even needed at this point.
        """

        raise NotImplementedError('Port class must implement __init__()')


    def test(self):
        """ Test port.

            Implementation of this method should test if e.g. hardware
            connected to this port is attached and works. If so, method should
            return anything. If not it should raise a descriptive exception
        """
        raise NotImplementedError('Port class must implement test()')


    def open(self):
        pass


    def close(self):
        pass


    def is_open(self):
        return True


    def read(self):
        pass


    def write(self, data):
        pass
