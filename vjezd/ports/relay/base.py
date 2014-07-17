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

""" Base Relay Port
    ===============
"""

import logging
logger = logging.getLogger(__name__)

from vjezd.ports.base import BasePort


class BaseRelay(BasePort):
    """ Base relay.

        As relay has configuration parameters in DB and they are non-dependent
        on a given relay class, this class provides methods which any relay can
        re-use in order to adhere to parameters. See the method descriptions
        below.

        Inherit from this class to get these methods in hardware-bound relay
        port class.

    """

    def __init__(self, *args):
        raise NotImplementedError


    def get_print_delay(self):
        """ Get delay in seconds before relay activation in print mode.

            Relay should wait given amount of seconds before activation when
            relay used from print mode (after printing ticket).
        """
        pass


    def get_scan_delay(self):
        """ Get delay in seconds before relay activation in scan mode.

            Relay should wait given amount of seconds before activation when
            relay used from scan mode (after scanning ticket).
        """
        pass


    def get_period(self):
        """ Get period between relay activation and deactivation.
        """
        # FIXME Not in specification
        pass


# Export port_class for port_factory()
port_class = LogRelay
