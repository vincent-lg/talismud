# Copyright (c) 2020-20201, LE GOFF Vincent
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.

"""Web session entity."""

import asyncio
from datetime import datetime
from pathlib import Path
import pickle
import typing as ty
from uuid import UUID, uuid4

from aiohttp_session import AbstractStorage, Session
from cryptography.fernet import Fernet, InvalidToken
from pony.orm import Optional, PrimaryKey, Required, Set

from data.base import db, PicklableEntity
from web.log import logger

secret_file = Path() / "settings" / "private.key"
if secret_file.exists():
    logger.debug("Load the Fernet secret key from file")
    with secret_file.open("rb") as file:
        SECRET_KEY = file.read()
else:
    logger.debug("Generate a new Fernet key")
    SECRET_KEY = Fernet.generate_key()
    with secret_file.open("wb") as file:
        file.write(SECRET_KEY)


FERNET = Fernet(SECRET_KEY)

class WebSession(PicklableEntity, db.Entity):

    """
    Web session entity.

    A web session is used to store data between requests.  Each
    request that doesn't have one yet gets a new session: a cookie is
    attached to the response containing the session ID, as a
    UUID.  When a request, originated from the same place, is sent,
    the cookie is read and the session retrieved.  Sessions can hold
    data, the logged in account for this request, for instance.
    Sessions expire after a time which depends, in part, on the
    cookie age and on the database policy.

    Data fields:
        uuid (UUID): the session ID (uuid4 is preferred).
        update_on (datetime): the last time the session was updated.
        account (Account, optional): the session account, if any.
                Note that the session account is the authenticated user.
        db_data (bytes): the data as an unpickled dictionary.

    Properties:
        data: read-only, retrieve the data as a dictionary.

    """

    uuid = PrimaryKey(UUID, default=uuid4)
    updated_on = Required(datetime, default=datetime.utcnow)
    account = Optional("Account")
    db_data = Required(bytes, default=pickle.dumps({}))

    @property
    def data(self):
        """Return the unpickled data as a dict."""
        return pickle.loads(self.db_data)
    @data.setter
    def data(self, data):
        self.db_data = pickle.dumps(data)


class PonyStorage(AbstractStorage):

    """Bridge between AIOHTTP sessions and PonyORM."""

    async def load_session(self, request):
        """Retrieve the WebSession data for a request."""
        cookie = self.load_cookie(request)
        if cookie is None:
            print("No cookie saved for this request, just create one.")
            return Session(None, data=None, new=True, max_age=self.max_age)
        else:
            token = cookie.encode()
            try:
                key = FERNET.decrypt(token)
            except InvalidToken:
                print("This is not a valid token", token)
                return Session(None, data=None, new=True, max_age=self.max_age)

            key = key.decode()
            try:
                uuid = UUID(key)
            except ValueError:
                session = None
            else:
                session = WebSession.get(uuid=uuid)

            if session is None:
                return Session(None, data=None, new=True, max_age=self.max_age)

            data = session.data
            print(f"Data for this session: {data}")
            return Session(key, data=data, new=False, max_age=self.max_age)

    async def save_session(self, request, response, session):
        """Save the session, writing the cookie."""
        key = session.identity
        if key is None:
            key = uuid4().hex
            encrypted = FERNET.encrypt(key.encode()).decode()
            print(f"this session doesn't exist, create a cookie (key={key}, enc={encrypted})")
            self.save_cookie(response, encrypted,
                    max_age=session.max_age)
        else:
            print(f"session {key} is empty")
            if session.empty:
                self.save_cookie(response, '', max_age=session.max_age)
            else:
                key = str(key)
                encrypted = FERNET.encrypt(key.encode()).decode()
                print(f"session {key} exists and the key is resaved in the cookie")
                self.save_cookie(response, encrypted,
                        max_age=session.max_age)

        data = self._get_session_data(session)
        try:
            uuid = UUID(key)
        except ValueError:
            return

        session = db.WebSession.get(uuid=uuid)
        if session is None:
            print("the session doesn't exist in PonyORM, create it.")
            session = db.WebSession(uuid=uuid)

        print(f"update session data to {data}")
        session.data = data
        session.updated_on = datetime.utcnow()

    def __get_store_key(self, key):
        return (self.cookie_name + '_' + key).encode('utf-8')
