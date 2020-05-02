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

"""Data service, responsible for the database."""

import asyncio
from pathlib import Path

from pony.orm import commit, db_session, set_sql_debug

from data.base import db
from service.base import BaseService
import settings

class Service(BaseService):

    """Data service."""

    name = "data"

    @property
    def has_admin(self):
        """
        Return whether there is an admin character in the database.

        An admin character has the "admin" permission (tag with category
        'permission') set.

        """
        return bool(db.CharacterTag.get(name="admin", category="permission"))

    async def init(self):
        """Asynchronously initialize the service."""
        self.init_task = None

    async def setup(self):
        """Set the database up."""
        self.init_task = asyncio.create_task(self.connect_to_DB())

    async def cleanup(self):
        """Clean the service up before shutting down."""
        if self.init_task:
            self.init_task.cancel()
        db_session.__exit__()

    async def connect_to_DB(self):
        """Try to connect to the database."""
        try:
            await self.init_DB()
        except asyncio.CancelledError:
            pass
        except Exception:
            self.logger.exception("data: an error occurred during initialization:")

    async def init_DB(self):
        """Initialize the database."""
        self.logger.debug("data: preparing to initialize the database.")
        file_path = (Path() / "talismud.db").absolute()
        db.bind(provider='sqlite', filename=str(file_path),
                create_db=True)
        set_sql_debug(True)
        db.generate_mapping(create_tables=True)
        self.logger.debug("data: database initialized.")
        self.init_task = None
        #Session.service = self
        #kredh = await Account.create(username="kredh", password=b"i", email="vincent.legoff.srs@gmail.com")
        #kredh = await Account.get(id=1).prefetch_related("session")
        #session = await Session.first().prefetch_related("account")

        # Open a DBSession and cached, to be persisted during all the
        # project lifetime.
        db_session._enter()

        # Create the START_ROOM and RETURN_ROOM if they don't exist
        start_room = return_room = None
        if db.Room.get(barcode=settings.START_ROOM) is None:
            start_room = db.Room(barcode=settings.START_ROOM,
                    title="Welcome to TalisMUD!")
            self.logger.info(f"The start room was created.")

        if db.Room.get(barcode=settings.RETURN_ROOM) is None:
            return_room = db.Room(barcode=settings.RETURN_ROOM,
                    title="A grey void")
            self.logger.info(f"The return room was created.")

        if start_room or return_room:
            commit()
        db.Delay.schedule()

    def create_session(self, session_id):
        """Create a new, empty session in the database, return it."""
        session = db.Session(uuid=session_id, context_path="connection.motd")
        return session
