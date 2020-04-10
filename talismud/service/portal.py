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
            return service.hosts

    async def init(self):
        """
        Asynchronously initialize the service.

        This method should be overridden in subclasses.  It is called by
        `start`` before sub-services are created.  It plays the role of
        an asynchronous constructor for the service, and service attributes
        often are created there for consistency.

        """
        self.game_id = None
        self.game_reader = None
        self.game_writer = None

    async def setup(self):
        """Set the portal up."""
        pass

    async def cleanup(self):
        """Clean the service up before shutting down."""
        pass

    async def error_read(self, writer):
        """Can't read from the connection."""
        if self.game_writer is writer:
            self.game_id = None
            self.game_reader = None
            self.game_writer = None
            self.logger.debug("The connection to the game is lost.")

    async def handle_register_game(self, reader):
        """A new game process wants to be registered."""
        writer = self.hosts.get(reader)
        if writer is None:
            self.logger.error("A game wishes to be registered but there's no active writer/reader pair for the socket.")
            return

        peer_name = writer.get_extra_info('peername')
        game_id = "UNKNOWN"
        if peer_name:
            peer_name = b":".join([str(name).encode() for name in peer_name])
            game_id = base64.b64encode(peer_name).decode()

        self.logger.debug(f"Receive register_game for ID={game_id}")
        self.game_id = game_id
        self.game_reader = reader
        self.game_writer = writer
        sessions = list(self.services["telnet"].sessions.keys())
        for writer in self.hosts.values():
            await self.services["crux"].send_cmd(writer, "registered_game",
                    dict(game_id=game_id, sessions=sessions))

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
        self.process.start_process("game")

    async def handle_stop_game(self, reader):
        """Handle the stop_game command."""
        crux = self.services["crux"]
        if self.game_writer:
            await crux.send_cmd(self.game_writer, "stop_game", dict(game_id=self.game_id))

        try:
            async with async_timeout(3):
                while self.game_id:
                    await crux.wait_for_cmd(self.game_reader, "*", 0.1)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass

        if self.game_id:
            self.logger.warning("The game process hasn't stopped, though it should have.")
        else:
            self.logger.debug("The game process has stopped.")

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
            self.logger.debug(f"Got {output!r} to session {session_id}.")
