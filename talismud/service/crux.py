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

"""Asynchronous messaging service."""

import asyncio

from service.base import BaseService
from service.mixins import CmdMixin

class Service(CmdMixin, BaseService):

    """
    CRUX service, creating a light messaging server.

    This service should be created by the portal (see `process/portal.py`).
    Each process can instantiate a `host` service, which is a client
    designed to connect to the CRUX.  The CRUX is a simple TCP server
    that can be used to trade data with the various processes.

    """

    name = "CRUX"

    async def init(self):
        """
        Asynchronously initialize the service.

        This method should be overridden in subclasses.  It is called by
        `start`` before sub-services are created.  It plays the role of
        an asynchronous constructor for the service, and service attributes
        often are created there for consistency.

        """
        await super().init()
        self.serving_task = None
        self.readers = {}
        self.writers = {}

    async def setup(self):
        """Set the CRUX server up."""
        self.schedule_hook("error_read", self.error_read)
        self.schedule_hook("error_write", self.error_write)
        self.serving_task = asyncio.create_task(self.create_server())

    async def cleanup(self):
        """Clean the service up before shutting down."""
        if self.serving_task:
            self.serving_task.cancel()

    async def create_server(self):
        """Create the CRUX server."""
        port = 4005
        self.logger.debug(f"CRUX: preparing to listen on localhost, port {port}")
        try:
            server = await asyncio.start_server(self.handle_connection,
                    '127.0.0.1', port)
        except asyncio.CancelledError:
            pass

        addr = server.sockets[0].getsockname()
        self.logger.debug(f"CRUX: Serving on {addr}")

        async with server:
            try:
                await server.serve_forever()
            except asyncio.CancelledError:
                pass
            except Exception:
                self.logger.exception("CRUX: An exception was raised when serving:")

    async def handle_connection(self, reader, writer):
        """Handle a new connection."""
        addr = writer.get_extra_info('peername')
        self.logger.debug(f"CRUX: {addr} has just connected.")
        self.readers[reader] = writer
        self.writers[writer] = reader
        try:
            await self.read_commands(reader)
        except asyncio.CancelledError:
            pass

    async def error_read(self, reader):
        """An error occurred when reading from reader."""
        writer = self.readers.pop(reader, None)
        if writer is None:
            self.logger.error(f"CRUX: connection was lost with a host, but the associated writer cannot be found.")
        else:
            self.writers.pop(writer)
            self.logger.warning("CRUX: connection to a host was closed.")
        await self.parent.error_read(writer)

    async def error_write(self, writer):
        """An error occurred when writing to writer."""
        reader = self.writers.pop(writer, None)
        if reader is None:
            self.logger.error(f"CRUX: connection was lost with a host, but the associated reader cannot be found.")
        else:
            self.readers.pop(reader)
            self.logger.warning("CRUX: connection to a host was closed.")
        await self.parent.error_write(writer)
