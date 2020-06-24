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

"""Game service."""

import asyncio

from data.base import db
from data.session import CMDS_TO_PORTAL, OUTPUT
from service.shell import Shell
from service.base import BaseService

CONSOLE = Shell({"db": db}, "<shell>")

class Service(BaseService):

    """Game main service."""

    name = "game"
    sub_services = ("host", "data", "web")

    async def init(self):
        """
        Asynchronously initialize the service.

        This method should be overridden in subclasses.  It is called by
        `start`` before sub-services are created.  It plays the role of
        an asynchronous constructor for the service, and service attributes
        often are created there for consistency.

        """
        self.game_id = None
        self.output_task = None
        self.cmds_task = None
        self.sessions = {}

    async def setup(self):
        """Set the game up."""
        self.services["host"].schedule_hook("connected", self.connected_to_CRUX)
        self.output_task = asyncio.create_task(self.spread_output())
        self.cmds_task = asyncio.create_task(self.spread_cmds_to_portal())

    async def cleanup(self):
        """Clean the service up before shutting down."""
        if self.output_task:
            self.output_task.cancel()
        if self.cmds_task:
            self.cmds_task.cancel()

    async def connected_to_CRUX(self, writer):
        """The host is connected to the CRUX server."""
        host = self.services["host"]
        data = self.services["data"]
        self.logger.debug("host: send register_game")
        await host.send_cmd(writer, "register_game",
                dict(pid=self.process.pid, has_admin=data.has_admin))

    async def error_read(self):
        """Cannot read from CRUX anymore, prepare to shut down."""
        self.logger.warning(f"A read error happened on the connection to CRUX, stop the process.")
        self.process.should_stop.set()

    async def error_write(self):
        """Cannot write to CRUX anymore, prepare to shut down."""
        self.logger.warning(f"A write error happened on the connection to CRUX, stop the process.")
        self.process.should_stop.set()

    async def spread_output(self):
        """Begin listening for the output queue."""
        try:
            await self.listen_for_output()
        except asyncio.CancelledError:
            pass
        except Exception:
            self.logger.exception("An error occurred while listening for the output queue:")

    async def listen_for_output(self):
        """Listen the output queue and send data accordingly."""
        host = self.services["host"]
        while True:
            session_id, text = await OUTPUT.get()

            if host.writer:
                await host.send_cmd(host.writer, "output", dict(
                        session_id=session_id, output=text))

    async def spread_cmds_to_portal(self):
        """Begin listening for the command queue."""
        try:
            await self.listen_for_cmds_to_portal()
        except asyncio.CancelledError:
            pass
        except Exception:
            self.logger.exception("An error occurred while listening for the command queue:")

    async def listen_for_cmds_to_portal(self):
        """Listen the command queue and send data accordingly."""
        host = self.services["host"]
        while True:
            cmd_name, args = await CMDS_TO_PORTAL.get()

            if host.writer:
                await host.send_cmd(host.writer, cmd_name, args)

    # Command handlers
    async def handle_registered_game(self, reader, game_id, sessions, **kwargs):
        """A new game process wants to be registered."""
        self.logger.debug(f"Receive registered_game for ID {game_id}")
        self.game_id = game_id

        # Remove all sessions except these that are explicitly
        # registered by the portal.
        to_delete = db.Session.select(lambda s: s.uuid not in sessions)
        count = to_delete.count()
        self.logger.debug(
                f"{count} session{'s' if count > 1 else ''} "
                f"{'are' if count > 1 else 'is'} to be deleted.")
        to_delete.delete(bulk=True)

    async def handle_stop_game(self, reader, game_id):
        """A new game process wants to be registered."""
        self.logger.debug(f"Receive stop_game for ID {game_id}")
        if self.game_id == game_id:
            self.logger.debug("Shutting down the game...")
            self.process.should_stop.set()

    async def handle_new_session(self, reader, session_id):
        """A new session is created."""
        self.logger.debug(f"A session of ID {session_id} has been created.")

        data = self.services["data"]
        session = data.create_session(session_id)
        self.sessions[session_id] = session
        await session.context.refresh()

    async def handle_input(self, reader, session_id, command):
        """Handle a received command from Telnet."""
        command = command.decode()

        # Try to find the session
        try:
            session = self.sessions[session_id]
        except KeyError:
            session = db.Session[session_id]
            self.sessions[session_id] = session
        context = session.context
        self.logger.debug(f"Received {command!r} from Telnet.")
        await context.handle_input(command)

    async def handle_create_admin(self, reader, username: str,
            password: str, email: str = ""):
        """
        Try to create an admin character and account.

        Args:
            reader (StreamReader): the reader for this command.
            username (str): the username to create.
            password (str): the plain text password to use.
            email (str, optional): the new account's email address.

        Response:
            The 'created_admin' command with the result.

        """
        filters = {
                "username": username,
        }

        if email:
            filters.update({
                    "email": email,
            })

        host = self.services["host"]
        if db.Account.get(**filters):
            if host.writer:
                await host.send_cmd(host.writer, "created_admin",
                        dict(success=False))

            return

        # Otherwise create the account
        account = db.Account.create_with_password(username, password, email)

        # Now create the character
        character = account.characters.create(name=username.title())

        # Give the new character admin permissions
        character.permissions.add("admin")
        if host.writer:
            await host.send_cmd(host.writer, "created_admin",
                    dict(success=True))
    async def handle_shell(self, reader, code: str):
        """
        Execute arbitrary Python code.

        Args:
            reader (StreamReader): the reader for this command.
            code (str): the Python code to execute.

        Response:
            The 'result' command with the output.

        """
        host = self.services["host"]
        more = CONSOLE.push(code)
        prompt = "... " if more else ">>> "

        if host.writer:
            await host.send_cmd(host.writer,
                    "result", dict(display=CONSOLE.output, prompt=prompt))
