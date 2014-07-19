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

# NOTE Avoid vjezd imports here. Put them into run() instead to avoid circular
# dependencies as this module is elementary

# Constants
NOT_EXITING = 0
EXITING = 1
CRIT_EXITING = 2

# Module internal variables
exiting_lock = threading.Lock()
exiting = NOT_EXITING
threads = []


def run():
    """ Run threads according to the device's own modes.

        This method will instantiate apropriate threads for all device operated
        modes and will start them. Then will be polling on them.
    """
    # Avoid circular dependencies
    from vjezd import crit_exit, exit
    from vjezd import device as this_device
    from vjezd.threads.print import PrintThread
    from vjezd.threads.scan import ScanThread

    if 'print' in this_device.modes:
        threads.append(PrintThread())
    if 'scan' in this_device.modes:
        threads.append(ScanThread())

    for t in threads:
        logger.debug('Starting thread {}'.format(t.name))
        t.start()

    while not exiting:
        # Check if all threads are still active
        for t in threads:
            logger.debug('Monitoring threads')
            if not t.is_alive():
                logger.critical('Thread {} is not alive. Exiting'.format(
                    t.name))
                crit_exit(10, force_thread=True)
            time.sleep(1)

    logger.info('Waiting for all threads to join')
    for t in threads:
        t.join()

    # Exit depending on exiting state
    if exiting == CRIT_EXITING:
        crit_exit(10)
    else:
        exit()


def set_exiting(state=EXITING):
    """ Method to set exiting flag thread-safely.
    """
    global exiting

    logger.debug('Waiting for exiting lock')
    with exiting_lock:
        if exiting != state:
            logger.debug('Setting exiting flag to {}'.format(state))
            exiting = state


def is_main_thread():
    """ Checks whether current thread is the MainThread.
    """

    return threading.current_thread() == threading.main_thread()
