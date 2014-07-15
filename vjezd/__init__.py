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
import signal
import getopt
import logging
logger = logging.getLogger(__name__)


# Python version check
v = sys.version_info
if v[0] < 3 or (v[0] == 3 and v[:2] < (3,3)):
    raise ImportError('Application requires Python 3.3 or above')
del v

# Release information
# FIXME perhaps load from generated file (e.g. from git tags)
__author__ = 'Ondrej Balaz'
__license__ = 'BSD'
__version__ = '1.0'

# Constants
# Application directory
# NOTE If there's a forced path to exisiting directory using VJEZD_APP_DIR
# environment variable use it. Otherwise use the directory where application
# main module is installed.
APP_DIR = os.getenv('VJEZD_APP_DIR')
if not APP_DIR or not os.path.isdir(APP_DIR):
    APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Application name
APP_NAME = os.path.basename(os.path.splitext(sys.argv[0])[0])
# Application version
APP_VER = __version__


def help():
    """ Show short help message.
    """

    print("""{appname} - entrance gate ticket control system
Usage: {appname} [options]

Available options:
(Mandatory arguments to long options are mandatory for short options too. Using
command line arguments overrides configuration file options.)
    --create-db             force the database to be re-created from scratch
                            WARNING: ALL EXISTING DATA WILL BE LOST!
-l, --log=FILENAME          path to log file, might be also syslog or stderr
-c, --config=FILENAME       path to configuration file
-m, --mode=MODE             device operation mode (scan, print, both, auto)
-i, --id=ID                 device identifier
-v, --verbose               increase verbosity, can be used multiple times
-h, --help                  show this short help message and exit
-V, --version               show version information and exit

Environment:
VJEZD_APP_DIR               application directory override (see also -d)

Report {appname} bugs to <support@blami.net>.
See COPYING for license information.""".format(
        appname=APP_NAME))


def version():
    """ Show version information.
    """

    print("""{appname} v{version}
Copyright (c) 2014 {author}. All rights reserved.
Licensed under the {license} license. See COPYING for more details.""".format(
        appname=APP_NAME,
        version=__version__,
        author=__author__,
        license=__license__))


def finalize():
    """ Finalize before exiting.
    """

    # NOTE This method is called even in state of crash so it must handle
    # corner cases very well.
    logger.info('Finalizing')

    from vjezd import ports
    from vjezd import db

    # Close DB connection
    db.finalize()


def crit_exit(code=1, err=None, force_thread=False):
    """ Exit program.

        :param is_thread bool:      Force thread behavior (for vjezd.threads)
    """

    # If possible log also relevant traceback
    tb = None
    if err and isinstance(err, Exception):
        import traceback
        tb = traceback.format_tb(err.__traceback__)
        if tb:
            logger.critical('Traceback (most recent call last):\n{}'.format(
                ''.join(tb)))

    # TODO send e-mail?
    # TODO restart?

    # If we aren't main thread just notify threads to exit
    from vjezd import threads
    if force_thread == True or not threads.is_main():
        # NOTE in case of force_thread == True thread name in log will be wrong
        logger.critical('Thread has failed! Exiting')
        threads.exiting = threads.CRIT_EXITING
    else:
        logger.critical('Application has failed! Exiting')

        finalize()
        sys.exit(code)


def exit(code=0):
    """ Exit program normally.
    """

    # Signal handlers are always executed in main thread and theres no way the
    # mode thread would exit app cleanly so we can exit directly.

    logger.info('Exiting')

    finalize()
    sys.exit(code)


def signal_handler(signum, frame):
    """ Handle signals.
    """

    from vjezd import threads

    logger.warning('Got handled signal: {}'.format(signum))

    if signum == signal.SIGINT:
        logger.warning('SIGINT. Interrupting threads might take a while...')
        threads.exiting = threads.EXITING


def main(args):
    """ Application entry point.
    """

    opt_logfile = None
    opt_loglevel = None
    opt_conf = None
    opt_mode = None
    opt_id = None

    # Process command line arguments
    try:
        opts, args = getopt.gnu_getopt(args,
            'l:c:m:i:vhV', [
                'log=',
                'conf=',
                'mode=',
                'id=',
                'verbose',
                'help',
                'version'])
    except getopt.GetoptError as err:
        print('error: {}'.format(err), file=sys.stderr)
        help()
        sys.exit(1)

    for opt, arg in opts:
        if opt in ('-l', '--log'):
            opt_logfile = arg
        elif opt in ('-c', '--conf'):
            opt_conf = arg
        elif opt in ('-m', '--mode'):
            if not arg.lower() in ('scan', 'print', 'both', 'auto'):
                print('error: mode must be one of scan, print, both, auto',
                    file=sys.stderr)
            opt_mode=arg.lower()
        elif opt in ('-i', '--id'):
            opt_id=arg
        elif opt in ('-v', '--verbose'):
            # verbosity maps to logging log level numeric values (default: 40)
            if opt_loglevel is None:
                opt_loglevel = 40
            elif opt_loglevel > 10:
                opt_loglevel -= 10
        elif opt in ('-h', '--help'):
            help()
            sys.exit()
        elif opt in ('-V', '--version'):
            version()
            sys.exit()

    # Install signal handlers
    signal.signal(signal.SIGINT, signal_handler)

    # Import our own modules here to avoid circular dependencies. Other modules
    # are imported after db.connect() as they use models
    from vjezd import conffile
    from vjezd import log
    from vjezd import db

    # Read configuration
    conffile.load(opt_conf)

    # Initialize logging and DB (create session and Base class)
    log.init(opt_logfile, opt_loglevel)
    db.init()

    # Import the rest of application modules
    from vjezd import ports
    from vjezd import device
    from vjezd import threads

    # Initialize ports as we need them to decide which mode device operates in
    # in case it is being set to auto.
    ports.init()

    # Initialize device
    device.init(opt_id, opt_mode)

    # Run threads
    threads.run()
