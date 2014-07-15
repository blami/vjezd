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


""" Logging
    *******

    Configuration Options
    ---------------------
    Logging is configured on a per-device basis and configuration is stored in
    the configuration file in [log] section. Following options are avaliable:

    level=
    A level of log verbosity, one of: CRITICAL, ERROR, WARNING, INFO or DEBUG
    listed from the lowest verbosity to the highest. Less-verbose level
    messages will be logged if more-verbose level is set (e.g. ERROR messages
    when WARNING is set).

    dest=
    One or more (comma-separated) destinations where log messages should be
    sent to. Destination can be an absolute path to log file, relative path
    to log file (which is then prepended by APP_DIR), 'console' which will send
    log messages to application standard error output or 'syslog' which will
    send log messages to system logging facility.

    append=
    If set to True messages will be appended to old log file, otherwise log
    file will be overwritten. This option has no effect for console or syslog
    destinations.
"""

import os
import sys
import logging
from logging import StreamHandler, FileHandler, NullHandler
from logging.handlers import SysLogHandler
logger = logging.getLogger(__name__)

from vjezd import APP_DIR, APP_NAME
from vjezd import conffile

# FIXME Setup very early logging that will just save messages and wait for
# log configuration will be fully read (and then flush them)

# Log message and date format
FORMAT='%(asctime)s %(levelname)s [%(name)s %(threadName)s ' \
    '%(funcName)s():%(lineno)d] %(message)s'
DATEFMT='%Y-%m-%d %H:%M:%S'


def init(path=None, level=None):
    """ Initialize the logging.

        :param string path:     Path to the log file
        :param string level:    Desired log level
    """
    logger.debug('Initializing logging')

    # Read configuration
    # Get log level. In case the level is non-valid logging level raise error
    if not level:
        level = getattr(logging, conffile.get('log', 'level', 'ERROR').upper(),
            None)
    # FIXME raise error if level is not valid?

    if not path:
        dests = conffile.get('log', 'dest', 'console').split(',')
    else:
        dests = [path]

    mode = 'w'
    if not path and conffile.getbool('log', 'append', False):
        mode = 'a'

    # Create handlers for all destinations
    handlers = []
    for dest in dests:
        if dest.lower() == 'console':
            handlers.append(StreamHandler(sys.stderr))
        elif dest.lower() == 'syslog':
            handlers.append(SysLogHandler())
        else:
            if not dest.startswith('/'):
                dest = os.path.join(APP_DIR, dest)
            handlers.append(FileHandler(dest, mode))

    if len(handlers) == 0:
        handlers.append(NullHandler())

    # Configure the logging facility
    logging.basicConfig(
        format=FORMAT,
        datefmt=DATEFMT,
        level=level,
        handlers=handlers)

    logger.debug('Log level is {}'.format(level))
    logger.debug('Logging initialized')

