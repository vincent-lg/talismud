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

"""Game service."""

import asyncio
from typing import Any

from command.layer import load_commands
from context.base import load_contexts
from data.base import db
from data.session import CMDS_TO_PORTAL, OUTPUT
from service.base import BaseService
from service.scripting import Scripting
from service.shell import Shell
import settings

CONSOLE = Shell({"db": db}, "<shell>")
SCRIPTING = Scripting()

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
        self.output_tasks = {}
        self.cmds_task = None
        self.sessions = {}
        self.messaging = MessagingCondition()

    async def setup(self):
        """Set the game up."""
        self.services["host"].schedule_hook("connected", self.connected_to_CRUX)
        self.output_tasks["unknown"] = asyncio.create_task(
                self.watch_unknown())
        self.cmds_task = asyncio.create_task(self.spread_cmds_to_portal())
        load_commands(self.messaging)
        load_contexts(self.messaging)

    async def cleanup(self):
        """Clean the service up before shutting down."""
        for uuid, task in tuple(self.output_tasks.items()):
            task.cancel()
            _ = self.output_tasks.pop(uuid, None)

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

    async def watch_unknown(self):
        """Begin listening for the unknown output queue."""
        try:
            await self.listen_for_unknown_output()
        except asyncio.CancelledError:
            pass
        except Exception:
            self.logger.exception(
                    "An error occurred while listening for the "
                    "unknown output queue:"
            )

    async def listen_for_unknown_output(self):
        """Listen the unknown output queue and log it."""
        queue = OUTPUT["unknown"]
        while True:
            text = await queue.get()

            # Log this, as this is an error
            self.logger.error(
                    "Text arrived on the unknown output queue and "
                    f"can't be delivered to its session:\n{text!r}"
            )

    async def spread_output(self, session):
        """Begin listening for the output queue."""
        try:
            await self.listen_for_output(session)
        except asyncio.CancelledError:
            pass
        except Exception:
            self.logger.exception(
                    "An error occurred while listening for the "
                    f"output queue of {session.uuid}:"
            )

    async def listen_for_output(self, session):
        """Listen to the output queue and send data accordingly."""
        host = self.services["host"]
        queue = OUTPUT[session.uuid]
        while True:
            text = await queue.get()

            # Before sending the messages, make sure the list of
            # running object is empty.
            messaging = self.messaging
            async with messaging:
                await messaging.wait_for(lambda: len(messaging.running) == 0)

            # Collect other messages from this session if available
            while not queue.empty():
                text += b"\n" + queue.get_nowait()

            # If appropriate, add the context prompt
            context = session.focused_context
            prompt = context.get_prompt()
            if prompt:
                text += b"\n" + prompt.encode(
                        session.options.get("encoding",
                        settings.DEFAULT_ENCODING), errors="replace")

            if host.writer:
                await host.send_cmd(host.writer, "output", dict(
                        session_id=session.uuid, output=text))

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

        # Recreate the output queues and output tasks for these sessions.
        for session in db.Session.select():
            uuid = session.uuid
            self.sessions[uuid] = session
            OUTPUT[uuid] = asyncio.Queue()
            self.output_tasks[uuid] = asyncio.create_task(
                    self.spread_output(session))

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
        OUTPUT[session_id] = asyncio.Queue()
        self.output_tasks[session_id] = asyncio.create_task(
                self.spread_output(session))
        await session.context.refresh()

    async def handle_disconnect_session(self, reader, session_id):
        """
        Handle when Telnet asks to disconnect a session.

        This is mostly useful when Telnet is aware a connection has
        ended, but the game doesn't yet know.  This usually happens
        in case of error.

        Args:
            session_id (Uuid): the session ID.

        """
        session = db.Session.get(uuid=session_id)
        if session:
            self.logger.info(f"Disconnect and delete the session {session_id}")
            task = self.output_tasks.pop(session_id, None)
            if task:
                task.cancel()
            _ = OUTPUT.pop(session_id, None)
            session.delete()

    async def handle_input(self, reader, session_id, command):
        """
        Handle a received command from a Telnet-like network.

        The specified command is bytes at this point.  It will be
        decoded using the session encoding
        (`session.storage["encoding"]`) if it exists, or the
        DEFAULT_ENCODING setting key.

        Args:
            session_id (uuid.UUID): the session ID.
            command (bytes): the command entered by the user.

        """
        # Try to find the session
        try:
            session = self.sessions[session_id]
        except KeyError:
            # Create it in the database
            session = db.Session[session_id]
            self.sessions[session_id] = session

        # Decode the command
        encoding = session.options.get("encoding", settings.DEFAULT_ENCODING)
        try:
            decoded = command.decode(encoding, errors="replace")
        except LookupError:
            # Use utf-8 as a default
            encoding = "utf-8"
            decoded = command.decode(encoding, errors="replace")

        # Send the decoded text to the session's active context
        context = session.context
        await context.handle_input(decoded)

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

    async def handle_scripting(self, reader, code: str):
        """
        Execute scripting code.

        Args:
            reader (StreamReader): the reader for this command.
            code (str): the scripting code to execute.

        Response:
            The 'result' command with the output.

        """
        host = self.services["host"]
        more = await SCRIPTING.push(code)
        prompt = "... " if more else ">>> "

        if host.writer:
            await host.send_cmd(host.writer,
                    "result", dict(display=SCRIPTING.output, prompt=prompt))


class MessagingCondition(asyncio.Condition):

    """A condition to keep track of current messages."""

    def __init__(self):
        super().__init__()
        self.running = set()

    async def mark_as_running(self, obj: Any):
        """
        Mark the specified object as running.

        This is usually called automatically by contexts and commands
        that start to run.  This would signal the condition to
        wait before delivering messages.  The condition will
        wait until all commands and contexts have mark themselves
        as done (see `mark_as_done`).

        Args:
            obj (Any): the running object (usually context or command).

        """
        self.running.add(obj)

    async def mark_as_done(self, obj: Any):
        """
        Mark this object as done.

        Usually this is called automatically when the context or command
        is done executing and messages should be sent.

        Args:
            obj (Any): the running object (context or command).

        """
        self.running.discard(obj)

        async with self:
            self.notify_all()
