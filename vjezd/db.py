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
    ********

    Installation
    ------------
    Application expects MySQL database engine to be installed on configured
    host, an empty database created and a dedicated role with full permissions
    for the database. Following is the minimal set of commands:

    Configuration Options
    ---------------------
    Database connection is configured per-device in the configuration file in
    section [db].
"""

import sys
import logging
logger = logging.getLogger(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError

from vjezd import APP_NAME, APP_VER
from vjezd import crit_exit
from vjezd import conffile


def init():
    """ Initialize the database connection.
    """
    logger.debug('Initializing DB connection')

    ci = get_connection_info()

    # Set SQL logger to same level as root logger
    logging.getLogger('sqlalchemy.engine').setLevel(
        logging.getLogger().getEffectiveLevel())

    # NOTE engine, session and Base aren't defined before calling init() which
    # makes application crash if db.init() wasn't called or failed. That's
    # intended behavior.

    # Create engine and session
    global engine
    global session
    engine = create_engine(ci)
    # NOTE See: http://flask.pocoo.org/docs/patterns/sqlalchemy/
    session = scoped_session(sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine))

    # Create declarative Base class for models
    global Base
    Base = declarative_base()
    Base.query = session.query_property()

    try:
        # Import all models and create/extend non-existent tables in DB
        # NOTE all models must be imported in models/__init__.py
        import vjezd.models

        Base.metadata.create_all(bind=engine)

        session.commit()
        session.remove()

    except SQLAlchemyError as err:
        logger.critical('Unable to access DB: {}'.format(err))
        crit_exit(2, err)

    logger.debug('DB connection initialized')


def finalize():
    """ Close the database connection.
    """
    logger.debug('DB connection closed')


def get_connection_info():
    """ Get the connection info from the configuration.
    """
    # Assemble connection info for MySQL Connector
    ci='mysql+mysqlconnector://{user}:{password}@{host}/{dbname}'.format(
        user=conffile.get('db', 'user', APP_NAME),
        password=conffile.get('db', 'password', APP_NAME),
        host=conffile.get('db', 'host', 'localhost'),
        dbname=conffile.get('db', 'dbname', APP_NAME))

    logger.info('DB connection info: {}'.format(ci))
    return ci


def install_schema(factory=False):
    """ Install schema.

        Create default values and constants in fresh schema tables.

        :param factory boolean:         Factory reset all defaults
    """
    pass
