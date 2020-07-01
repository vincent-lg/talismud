# Copyright (c) 2020, LE GOFF Vincent
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

"""Bridge AIOHTTP sessions and PonyORM."""

from datetime import datetime, timedelta
import uuid

from aiohttp_session import AbstractStorage, Session

from data.base import db

class PonyStorage(AbstractStorage):
    def __init__(self, *, cookie_name="AIOHTTP_SESSION",
                 domain=None, max_age=None, path='/',
                 secure=None, httponly=True,
                 encoder=lambda x: x, decoder=lambda x: x):
        super().__init__(cookie_name=cookie_name, domain=domain,
                         max_age=max_age, path=path, secure=secure,
                         httponly=httponly,
                         encoder=encoder, decoder=decoder)

    async def load_session(self, request):
        cookie = self.load_cookie(request)
        print(f"cookie: {cookie}")
        if cookie is None:
            print("No cookie saved for this request, just create one.")
            return Session(None, data=None, new=True, max_age=self.max_age)
        else:
            key = str(cookie)
            session = db.Session.get(uuid=uuid.UUID(key))
            if session is None:
                return Session(None, data=None,
                               new=True, max_age=self.max_age)

            data = session.storage.get("web_data", {})
            print(f"Data for this session: {data}")
            return Session(key, data=data, new=False, max_age=self.max_age)

    async def save_session(self, request, response, session):
        key = session.identity
        if key is None:
            key = uuid.uuid4().hex
            print(f"this session doesn't exist, create a cookie (key={key}) for it")
            self.save_cookie(response, key,
                             max_age=session.max_age)
        else:
            print(f"session {key} is empty")
            if session.empty:
                self.save_cookie(response, '',
                                 max_age=session.max_age)
            else:
                key = str(key)
                print(f"session {key} exists and the key is resaved in the cookie")
                self.save_cookie(response, key,
                                 max_age=session.max_age)

        data = self._get_session_data(session)
        expire = datetime.utcnow() + timedelta(seconds=session.max_age) \
            if session.max_age is not None else None
        session = db.Session.get(uuid=uuid.UUID(key))
        if session is None:
            print("the session doesn't exist in PonyORM, create it.")
            session = db.Session(uuid=uuid.UUID(key), context_path=".web")
        print(f"update session data to {data}")
        session.storage["web_data"] = data

    def __get_store_key(self, key):
        return (self.cookie_name + '_' + key).encode('utf-8')
