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

""" Threads
    #######

    This module contains implementation of threads handling the device modes.
    Each mode has its own lifecycle implemented in thread.
"""


import time
import threading
import logging
logger = logging.getLogger(__name__)

from vjezd import crit_exit, exit
from vjezd import device

# Constants
NOT_EXITING = 0
EXITING = 1
CRIT_EXITING = 2

# Globals
exiting = NOT_EXITING
threads = []


def run():
    """ Run threads according to the device's own modes.

        This method will instantiate apropriate threads for all device operated
        modes and will start them. Then will be polling on them.
    """

    # Avoid circular dependencies
    from vjezd.threads.print_thread import PrintThread
    from vjezd.threads.scan_thread import ScanThread

    if 'print' in device.device.modes:
        threads.append(PrintThread())
    if 'scan' in device.device.modes:
        threads.append(ScanThread())

    for thread in threads:
        logger.debug('Running thread {}'.format(thread.name))
        try:
            thread.start()
        except Exception as err:
            logger.crit('Cannot start thread {}: {}'.format(thread.name, err))
            crit_exit(10, err, force_thread=True)

    # Superseed running threads
    while not exiting:
        # Check if all threads are still active
        for thread in threads:
            if not thread.is_alive():
                logger.critical('Thread {} has died'.format(thread.name))
                crit_exit(10, force_thread=True)
        time.sleep(2)

    logger.info('Exiting. Waiting for threads to join...')
    for thread in threads:
        thread.join()

    # Exit depending on exiting state
    if exiting == CRIT_EXITING:
        crit_exit(10)
    else:
        exit()


def is_main():
    """ Checks whether current thread is the MainThread.
    """

    return threading.current_thread() == threading.main_thread()
