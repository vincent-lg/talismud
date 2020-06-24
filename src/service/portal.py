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

"""Portal service."""

import asyncio
import base64
import time
from uuid import UUID

from async_timeout import timeout as async_timeout

from service.base import BaseService

class Service(BaseService):

    """Portal service."""

    name = "portal"
    sub_services = ("crux", "telnet")

    @property
    def hosts(self):
        """Return the hosts of the CRUX service."""
        service = self.services.get("crux")
        if service:
            return service.readers

    async def init(self):
        """
        Asynchronously initialize the service.

        This method should be overridden in subclasses.  It is called by
        `start`` before sub-services are created.  It plays the role of
        an asynchronous constructor for the service, and service attributes
        often are created there for consistency.

        """
        self.game_id = None
        self.game_pid = None
        self.game_process = None
        self.game_reader = None
        self.game_writer = None
        self.return_code_task = None

    async def setup(self):
        """Set the portal up."""
        pass

    async def start_watch_return_code(self):
        """Start the task to watch the return code."""
        self.return_code_task = asyncio.create_task(self.watch_return_code())

    async def cleanup(self):
        """Clean the service up before shutting down."""
        await self.cleanup_watch_return_code()

    async def cleanup_watch_return_code(self):
        """Stop watching the process' return code."""
        if self.return_code_task:
            self.return_code_task.cancel()

    async def error_read(self, writer):
        """Can't read from the connection."""
        if self.game_writer is writer:
            self.game_id = None
            self.game_reader = None
            self.game_writer = None
            self.logger.debug("The connection to the game is lost.")
            crux = self.services["crux"]
            for writer in crux.readers.values():
                await crux.send_cmd(writer, "game_stopped")
    error_write = error_read

    async def check_eof(self, reader):
        """Check if EOF has been sent."""
        if reader.at_eof():
            if reader is self.game_reader:
                await self.error_read(self.game_writer)

    async def watch_return_code(self):
        """Asynchronously watch for the game process' return code."""
        try:
            while True:
                await asyncio.sleep(0.2)
                if self.game_process:
                    return_code = self.game_process.poll()
                    if return_code is None:
                        continue
                    elif return_code != 0:
                        error = self.game_process.communicate()[1]
                        error = error.decode("utf-8", errors="replace")
                        error = error.replace("\r\n", "\n")
                        error = error.replace("\r", "\n").rstrip()
                        crux = self.services["crux"]
                        for writer in crux.readers.values():
                            await crux.send_cmd(writer, "cannot_start_game",
                                    dict(error=error))
                        break
                    #else:
                    #    break()
        except asyncio.CancelledError:
            pass
    async def handle_register_game(self, reader, pid, has_admin=False):
        """
        A new game process wants to be registered.

        Args:
            reader (StreamReader): the reader associated with this command.
            pid (int): the game's Process ID.
            has_admin (bool, optional): whether an admin character exists.

        On receiving this command, the portal will try to create a
        unique identifier for the game, based on network information.
        It will then broadcast a `registered_game` to all, with this ID.

        """
        writer = self.hosts.get(reader)
        if writer is None:
            self.logger.error("A game wishes to be registered but there's no active writer/reader pair for the socket.")
            return

        peer_name = writer.get_extra_info('peername')
        game_id = "UNKNOWN"
        if peer_name:
            peer_name = b":".join([str(name).encode() for name in peer_name])
            game_id = base64.b64encode(peer_name).decode()

        self.logger.debug(f"Receive register_game for ID={game_id}, PID={pid}")
        self.game_id = game_id
        self.game_pid = pid
        self.game_reader = reader
        self.game_writer = writer
        await self.cleanup_watch_return_code()
        sessions = list(self.services["telnet"].sessions.keys())
        for writer in tuple(self.hosts.values()):
            await self.services["crux"].send_cmd(writer, "registered_game",
                    dict(game_id=game_id, sessions=sessions,
                    pid=pid, has_admin=has_admin))

    async def handle_what_game_id(self, reader):
        """Return the game ID to the one querying for it."""
        crux = self.services["crux"]
        writer = self.hosts.get(reader)
        if writer is None:
            self.logger.error("A host wishes for the game_id, but the host writer can't be found.")
            return

        await crux.send_cmd(writer, "game_id", dict(game_id=self.game_id))

    async def handle_start_game(self, reader):
        """Handle the start_game command."""
        if self.game_pid:
            # The game is already running
            self.logger.debug(
                f"The game process (PID={self.game_pid}) hasn't "
                "stopped yet.  Wait..."
            )

            # Note: this will block instead of running asynchronously.
            # Not ideal, but it's hard to tell how much time this will
            # take, as the game might have a lot of data to save on shutdown.
            self.game_process.wait()
            self.game_pid = None
            self.game_process = None

        await self.cleanup_watch_return_code()
        self.game_process = self.process.start_process("game")
        await self.start_watch_return_code()

    async def handle_stop_game(self, reader):
        """Handle the stop_game command."""
        crux = self.services["crux"]
        if self.game_writer:
            self.logger.debug(f"Sending 'stop_game' to game ID {self.game_id}...")
            await crux.send_cmd(self.game_writer, "stop_game", dict(game_id=self.game_id))
        else:
            self.logger.warning("Can't stop the game, it's already down it seems.")
            crux = self.services["crux"]
            for writer in crux.readers.values():
                await crux.send_cmd(writer, "game_stopped")
            return

        begin = time.time()
        while time.time() - begin < 3 and self.game_id:
            await crux.wait_for_cmd(self.game_reader, "*", 0.5)
            if self.game_reader:
                await self.check_eof(self.game_reader)

        if self.game_id:
            self.logger.warning("The game process hasn't stopped, though it should have.")
        else:
            self.logger.debug("The game process has stopped.")

    async def handle_restart_game(self, reader, announce=True):
        """Restart the game."""
        self.logger.debug("Asked to restart the game...")
        if announce:
            # Announce to all contected clients
            telnet = self.services["telnet"]
            for session_id in telnet.sessions.keys():
                await telnet.write_to(session_id, "Restarting the game ...")

        await self.handle_stop_game(reader)
        origin = time.time()
        while time.time() - origin < 5:
            if self.game_id is None:
                self.logger.debug("The game was stopped, now start it again.")
                await self.handle_start_game(reader)
                break

            await asyncio.sleep(0.1)

        # Wait for the game to register again
        origin = time.time()
        while time.time() - origin < 5:
            if self.game_id:
                break

            await asyncio.sleep(0.1)

        if not self.game_id:
            self.logger.warning("The game should have started by now.")

        if announce and self.game_id:
            # Announce to all contected clients
            telnet = self.services["telnet"]
            for session_id in telnet.sessions.keys():
                await telnet.write_to(session_id, "... game restarted!")

    async def handle_stop_portal(self, reader):
        """Handle the stop_portal command."""
        await self.handle_stop_game(reader)
        self.process.should_stop.set()

    async def handle_output(self, reader, session_id, output):
        """Send the output to the client."""
        _, writer = self.services["telnet"].sessions.get(session_id, (None, None))
        if writer is None:
            self.logger.warning(f"telnet: should send to session {session_id}, but can't find an appropriate writer.")
        else:
            writer.write(output)
            await writer.drain()

    async def handle_disconnect_session(self, reader, session_id: UUID):
        """
        Disconnect the given session from Telnet service.

        Args:
            session_id (UUID): the session ID to disconnect.

        If important, the reason should have been given beforehand.

        """
        telnet = self.services["telnet"]
        await telnet.disconnect_session(session_id)

    async def handle_create_admin(self, reader, username: str,
            password: str, email: str = ""):
        """
        Send a 'create_admin' command to the game, to create a new admin.

        Args:
            reader (StreamReader): the reader for this command.
            username (str): the username to create.
            password (str): the plain text password to use.
            email (str, optional): the new account's email address.

        Response:
            The 'created_admin' command with the result.

        """
        crux = self.services["crux"]
        if self.game_writer:
            self.logger.debug(f"Sending 'create_admin' to game ID {self.game_id}...")
            await crux.send_cmd(self.game_writer, "create_admin",
                    dict(username=username, password=password, email=email))

        success, args = await crux.wait_for_cmd(self.game_reader,
                "created_admin", timeout=60)
        writer = self.hosts.get(reader, None)
        if writer:
            await crux.send_cmd(writer, "created_admin", dict(success=success))

    async def handle_created_admin(self, reader, success: bool):
        """
        When the portal receives 'created_admin', do nothing.

        This response is expected from the 'create_admin' handler.
        Intercepting this response while 'create_admin' hasn't been
        sent isn't of much use.

        """
        pass

    async def handle_shell(self, reader, code: str):
        """
        Send a 'shell' command to the game, to execute Python code.

        Args:
            reader (StreamReader): the reader for this command.
            code (str): the Python code to execute.

        Response:
            The 'result' command with the output.

        """
        crux = self.services["crux"]
        if self.game_writer:
            self.logger.debug(f"Sending 'shell' to game ID {self.game_id}...")
            await crux.send_cmd(self.game_writer, "shell", dict(code=code))

        success, args = await crux.wait_for_cmd(self.game_reader, "result")
        writer = self.hosts.get(reader, None)
        if success and writer:
            await crux.send_cmd(writer, "result", args)

    async def handle_result(self, reader, **kargs):
        """
        When the portal receives 'result', do nothing.

        This response is expected from the 'shell' handler.
        Intercepting this response while 'shell' hasn't been
        sent isn't of much use.

        """
        pass
