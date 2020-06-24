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

"""Telnet server."""

import asyncio
from io import BytesIO
from typing import Union
from uuid import UUID, uuid4

from service.base import BaseService
from service.mixins import CmdMixin
import settings

class Service(CmdMixin, BaseService):

    """
    Telnet server to await for TCP connections from users.

    This should be run from the portal service.  Commands (user input)
    are sent to CRUX (running on the game process) and answers are sent
    in the same way.

    """

    name = "telnet"

    async def init(self):
        """Asynchronously initialize the service."""
        self.serving_task = None
        self.sessions = {}
        self.readers = {}
        self.buffers = {}
        self.current_id = 1
        self.CRUX = None

    async def setup(self):
        """Set the CRUX server up."""
        self.CRUX = self.parent.services["crux"]
        self.serving_task = asyncio.create_task(self.create_server())

    async def cleanup(self):
        """Clean the service up before shutting down."""
        if self.serving_task:
            self.serving_task.cancel()

    async def create_server(self):
        """Create the CRUX server."""
        interface = "0.0.0.0" if settings.PUBLIC_ACCESS else "127.0.0.1"
        port = settings.TELNET_PORT
        self.logger.debug(
            f"telnet: preparing to listen on {interface}, port {port}"
        )
        try:
            server = await asyncio.start_server(self.new_connection,
                    interface, port)
        except asyncio.CancelledError:
            pass
        except ConnectionError:
            self.logger.error("telnet: can't connect to {interface}:{port}")
            return

        addr = server.sockets[0].getsockname()
        self.logger.debug(f"telnet: Serving on {addr}")

        async with server:
            try:
                await server.serve_forever()
            except asyncio.CancelledError:
                pass
            except Exception:
                self.logger.exception("telnet: An exception was raised when serving:")

    async def new_connection(self, reader, writer):
        """Handle a new connection."""
        try:
            await self.begin_reading_from(reader, writer)
        except asyncio.CancelledError:
            return
        except Exception:
            self.logger.exception("telnet: an error occurred when reading a stream:")

    async def begin_reading_from(self, reader, writer):
        """Begin to read from a given connection."""
        addr = writer.get_extra_info('peername')
        session_id = uuid4()
        await self.new_session(session_id, reader, writer)

        try:
            await self.read_input(reader)
        except asyncio.CancelledError:
            pass

    async def read_input(self, reader):
        """Enter an asynchronous loop to read input from `reader`."""
        session_id, _ = self.readers.get(reader, (None, None))
        if session_id is None:
            self.logger.warning("Trying to listen on a client with no session ID.")
            return

        # Creates the buffer for the reader if it doesn't exist:
        buffer = self.buffers.get(reader)
        if buffer is None:
            buffer = BytesIO()
            self.buffers[reader] = buffer

        while True:
            try:
                data = await reader.read(1024)
            except ConnectionError:
                await self.error_read(reader)
                return
            except asyncio.CancelledError:
                return
            except Exception:
                self.logger.exception("An exception was raised on read_commands")
                await self.error_read(reader)
                return

            if not data:
                # The socket has been disconnected
                await self.error_read(reader)
                return

            buffer.write(data)

            # Process full lines, placing incomplete lines in the buffer
            buffer.seek(0)
            unprocessed = b""
            while line := buffer.readline():
                # Windows \r\n are replaced with \n
                line = line.replace(b"\r\n", b"\n")
                # MAC \r are replaced by \n
                line.replace(b"\r", b"\n")

                # Now all should be Unix-like simple \n
                if b"\n" in line:
                    for piece in line.splitlines():
                        # It is possible, though unlikely, that this loop
                        # will be called more than once.
                        self.logger.debug(f"Process: {piece!r}.")
                        await self.send_input(session_id, piece)
                else:
                    unprocessed = line

            # Empty the buffer, add only the unprocessed bytes
            buffer.seek(0)
            buffer.truncate()
            buffer.write(unprocessed)

    async def error_read(self, reader):
        """An error occurred when reading from reader."""
        session_id, writer = self.readers.pop(reader, (0, None))
        if writer is None:
            self.logger.error(f"telnet: connection was lost with a client, but the associated writer cannot be found.")
        else:
            self.logger.debug(f"telnet: the connection to a client {session_id} was closed.")

            try:
                del self.sessions[session_id]
            except KeyError:
                pass

    async def new_session(self, session_id, reader, writer):
        """
        Process a new session.

        Args:
            session_id (int): the session identifier.
            reader (StreamReader): the session reader.
            writer (StreamWriter): the session writer.

        """
        self.logger.debug(f"telnet: new connection, session ID {session_id}")
        self.sessions[session_id] = (reader, writer)
        self.readers[reader] = (session_id, writer)
        writer = self.parent.game_writer
        if writer:
            await self.CRUX.send_cmd(writer, "new_session", dict(session_id=session_id))

    async def disconnect_session(self, session_id: UUID):
        """
        Disconnect the given session.

        Args:
            session_id (UUID): the session to disconnect.

        """
        reader, writer = self.sessions.pop(session_id, (None, None))
        if writer:
            self.logger.debug(f"Diconnection session ID {session_id}.")
            writer.close()
            await writer.wait_closed()

    async def send_input(self, session_id: int, command: bytes):
        """Called when an input line was sent by the client."""
        writer = self.parent.game_writer
        if writer:
            await self.CRUX.send_cmd(writer, "input", dict(session_id=session_id, command=command))

    async def write_to(self, session_id: UUID, message: Union[str, bytes]):
        """
        Send a message to this session.

        Args:
            session_id (UUID): the session ID.
            message (str or bytes): the message to send.  If a
                    str, encode it using the default encoding
                    in the settings.

        Should this method fail, the session will be disconnected.

        """
        if isinstance(message, str):
            message = message.replace("\r\n", "\n").replace("\r", "\n")
            message = message.encode(settings.DEFAULT_ENCODING,
                    errors="replace")
        else:
            message = message.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        if not message.endswith(b"\n"):
            message += b"\n"

        message = message.replace(b"\n", b"\r\n")

        reader, writer = self.sessions.get(session_id, (None, None))
        if writer:
            try:
                writer.write(message)
                await writer.drain()
            except ConnectionError:
                await self.error_read(reader)
                return
