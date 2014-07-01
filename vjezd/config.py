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

""" Configuration
"""

import os
import sys
import configparser
import logging
logger = logging.getLogger(__name__)

from vjezd import APP_DIR, APP_NAME


config = configparser.ConfigParser()


def load_from_file(path=None, append=True):
    """ Load configuration file.

        Configuration files are not merged. This method reads just one of them.

        :param str path:                path to the configuration file
        :param bool append:             append loaded options to registry
                                        instead of replacing registry
    """

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
    if not append:
        for s in config.sections():
            config.remove_section(s)

    # Read configuration
    config.read(path)


def get(section, option, fallback=None, *, raw=False, vars=None, type=None):
    """ Get value for given option in fiven section.
    """

    # Select appropriate coerce method to the given type
    method = config.get
    if type == bool:
        method = config.getboolean
    elif type == int:
        method = config.getint
    elif type == float:
        method = config.getfloat

    # Invoke appropriate method for given type
    return method(section, option, raw=raw, vars=vars, fallback=fallback)


def getbool(section, option, fallback=None, *, raw=False, vars=None):
    """ A convenience method which coerces option value to a Boolean value.
    """
    return get(section, option, fallback, raw=raw, vars=vars, type=bool)


def getint(section, option, fallback=None, *, raw=False, vars=None):
    """ A convenience method which coerces option value to an Integer value.
    """
    return get(section, option, fallback, raw=raw, vars=vars, type=int)


def getfloat(section, option, fallback=None, *, raw=False, vars=None):
    """ A convenience method which coerces option value to a Float value.
    """
    return get(section, option, fallback, raw=raw, vars=vars, type=float)

