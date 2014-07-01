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

""" Database

    Database Configuration Options
    ------------------------------
    Database connection is configured per-device in the configuration file in
    section [db].
"""

import sys
import logging
logger = logging.getLogger(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from vjezd import APP_NAME
from vjezd import config


def init():
    """ Initialize the database connection.
    """

    ci = get_connection_info()

    # NOTE engine, session and Base aren't defined before calling init() which
    # makes application crash if db.init() wasn't called or failed. That's
    # intended behavior.

    # create engine and session
    global engine
    global session
    engine = create_engine(ci)
    # NOTE thread safe, see: http://flask.pocoo.org/docs/patterns/sqlalchemy/
    session = scoped_session(sessionmaker(
        autocommit=False,
        autoflush=True,
        bind=engine,
        ))

    # create declarative base class for models
    global Base
    Base = declarative_base()
    Base.query = session.query_property()

    # import all model modules, create all tables
    # NOTE it is necessary to import any new model in models/__init__.py!
    from vjezd import models
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as err:
        logger.critical('Cannot create schema. Exiting.\n{}'.format(err))
        sys.exit(1)


def get_connection_info():
    """ Get connection info from the configuration.
    """

    # Assemble connection info for MySQL Connector
    ci='mysql+mysqlconnector://{user}:{password}@{host}/{dbname}'.format(
        user=config.get('db', 'user', APP_NAME),
        password=config.get('db', 'password', APP_NAME),
        host=config.get('db', 'host', 'localhost'),
        dbname=config.get('db', 'dbname', APP_NAME),
        )

    logger.info('Database connection info: {}'.format(ci))
    return ci

