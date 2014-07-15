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

""" Local Configuration File
    ************************

    Local configuration file stores any local device-specific configuration
    such as device identifier, logging settings or database connection
    settings.
"""

import os
import sys
import configparser
import logging
logger = logging.getLogger(__name__)

from vjezd import APP_DIR, APP_NAME

conffile = configparser.ConfigParser()


def load(path=None):
    """ Load configuration file.

        :param str path:                path to the configuration file
    """
    logger.debug('Loading local configuration')

    if not path:
        # Standard configuration directories, first has the highest priority
        confdirs = (
            '/etc',
            '/etc/{}'.format(APP_NAME),
            APP_DIR)
        for confdir in confdirs:
            confpath = os.path.join(confdir, '{}.conf'.format(APP_NAME))
            # First existing configuration file sets the path and breaks cycle
            if os.path.isfile(confpath):
                path = confpath
                break

    # Remove previous configuration
    if conffile.sections():
        logger.debug('Removing exisitng configuration file options')
        for s in conffile.sections():
            conffile.remove_section(s)

    # Read configuration
    # FIXME handle exceptions
    conffile.read(path)

    logger.debug('Configuration file successfuly loaded: {}'.format(path))


def get(section, option, fallback=None, type=None):
    """ Get value for given option in fiven section.
    """

    # Select appropriate coerce method to the given type
    method = conffile.get
    if type == bool:
        method = conffile.getboolean
    elif type == int:
        method = conffile.getint
    elif type == float:
        method = conffile.getfloat

    # Invoke appropriate method for given type
    return method(section, option, fallback=fallback)


def getbool(section, option, fallback=None):
    """ A convenience method which coerces option value to a Boolean value.
    """
    return get(section, option, fallback, type=bool)


def getint(section, option, fallback=None):
    """ A convenience method which coerces option value to an Integer value.
    """
    return get(section, option, fallback, type=int)


def getfloat(section, option, fallback=None):
    """ A convenience method which coerces option value to a Float value.
    """
    return get(section, option, fallback, type=float)

