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

""" Base Thread
    ===========
"""

import threading
import logging
logger = logging.getLogger(__name__)

from vjezd import crit_exit
from vjezd import threads


class BaseThread(threading.Thread):
    """ Abstract base class for threads.

        Each thread implementation should use BaseThread as a predcessor in
        order to have sensible thread name, exiting flag processing.
    """

    def __init__(self):
        """ Initialize print thread.
        """
        threading.Thread.__init__(self)
        self.name = self.__class__.__name__


    def run(self):
        """ Run thread.
        """
        try:
            while not threads.exiting:
                self.do()
                if threads.exiting:
                    logger.debug('Thread {} is exiting'.format(self.name))

        except Exception as err:
            logger.critical('Thread {} has failed: {}'.format(self.name, err))
            crit_exit(11, err)


    def do(self):
        """ Abstract worker method of thread.
        """
        raise NotImplementedError
