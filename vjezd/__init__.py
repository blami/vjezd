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

""" Vjezd is an application for 
"""

import os
import sys
import logging
logger = logging.getLogger(__name__)


# Python version check
v = sys.version_info
if v[0] < 3 or (v[0] == 3 and v[:2] < (3,3)):
    raise ImportError('Application requires Python 3.3 or above')
del v

# Release information
__author__ = 'Ondrej Balaz'
__license__ = 'BSD'
__version__ = '1.0'

# Constants
#: Application directory
# NOTE If there's a forced path to exisiting directory using VJEZD_APP_DIR
# environment variable use it. Otherwise use the directory where application
# main module is installed.
APP_DIR = os.getenv('VJEZD_APP_DIR')
if not APP_DIR or not os.path.isdir(APP_DIR):
    APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
#: Application name
APP_NAME = os.path.basename(os.path.splitext(sys.argv[0])[0])


from vjezd import config
from vjezd import log
from vjezd import db


def help():
    """ Show short help message.
    """

    print("""{appname} - entrance gate ticket control system
Usage: {appname} [options]

Available options:
(Mandatory arguments to long options are mandatory for short options too.)
-l, --log=FILENAME          path to log file, might be also syslog or stderr
-c, --config=FILENAME       path to configuration file
-v, --verbose               increase verbosity, can be used multiple times
-h, --help                  show this short help message and exit
-V, --version               show version information and exit

Environment:
VJEZD_APP_DIR               application directory override (see also -d)

Report {appname} bugs to <support@blami.net>.
See COPYING for license information.""".format(
        appname=APP_NAME,
    ))


def version():
    """ Show version information.
    """

    print("""{appname} v{version}
Copyright (c) 2014 {author}. All rights reserved.
Licensed under the {license} license. See COPYING for more details.""".format(
        appname=APP_NAME,
        version=__version__,
        author=__author__,
        license=__license__
    ))


def main(args):
    """ Application entry point.
    """

    # TODO getopt

    # Read configuration
    config.load_from_file()

    # Initialize logging and database
    log.init()
    db.init()
