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

"""Asynchronous messaging service for a client."""

import asyncio
import time

from async_timeout import timeout

from service.base import BaseService
from service.mixins import CmdMixin

class Service(CmdMixin, BaseService):

    """
    Host service, creating a light messaging client to connect to CRUX.

    Each process can instantiate a host service, which is a client
    designed to connect to the CRUX.  The CRUX is a simple TCP server
    that can be used to trade data with the various processes.

    Data from host to CRUX and reciprocally is in the form of commands.
    A command (sometimes called a 'CRUX command') is a pickled tuple
    containing two information: the command name as a string and
    the command arguments wrapped in a dictionary.  To react to
    a command, the host service or a parent service must define a method,
    named `handle_{command name}`, taking as argument the reader and
    the argument keys of the command.

    For instance, when a game asks CRUX to be registered, CRUX will send
    a confirmation as a command: the command's name is `registered_game`,
    and the argument is a dictionary `{'game_id': ...}` where the ID of the
    game is sent.  Therefore, to intercept this command, the game service
    must define a method `handle_registered_game` with `game_id` as argument:

        async def handle_registered_game(self, reader, game_id):
            ...

    See `CmdMixin` (service/cmd.py) for the communication methods.

    """

    name = "host"

    async def init(self):
        """Asynchronously initialize the service."""
        await super().init()

        # Since the host is responsible for ONE connection (between the
        # current process and CRUX), it is either connected, with a reader
        # and writer, or not connected at all.
        self.connected = False
        self.writer = None
        self.reader = None

        # Service configuration: this can be changed by parent services:
        self.max_attempts = 10 # Maximum of attempts when trying to connect
        self.timeout = 0.5 # Maximum timeout of a single connection attempt
        self.connect_on_startup = True # Connect to CRUX when the service starts

        # Keep track of the asynchronous tasks, to cancel them if needed:
        self.connecting_task = None
        self.reading_task = None

        # Create hooks to be called in specific situations:
        self.register_hook("cannot_connect") # Can't connect to CRUX
        self.register_hook("connected") # Has successfully connected to CRUX

    async def setup(self):
        """Set the host client up."""
        # If the host service can't read, calls `error_read` asynchronously:
        self.schedule_hook("error_read", self.error_read)
        self.schedule_hook("error_write", self.error_write)

        # Create the task to connect to CRUX
        self.connecting_task = asyncio.create_task(self.work_with_CRUX())

    async def cleanup(self):
        """Clean the host service up."""
        if self.connecting_task:
            self.connecting_task.cancel()
        if self.reading_task:
            self.reading_task.cancel()

        # Close the connection with the host
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()

    async def work_with_CRUX(self):
        """Attempt to connect to CRUX, if needed."""
        try:
            await self.connect_to_CRUX(startup=True)
        except Exception:
            self.logger.exception("host: an exception occurred:")

    async def connect_to_CRUX(self, startup=False):
        """
        Attempt to connect to the CRUX server.

        Args:
            startup (bool, optional): is it startup time?

        """
        if startup and not self.connect_on_startup:
            return

        if self.connected:
            self.logger.warning(f"host: the service is already connected to CRUX.")
            return

        max_attempts = self.max_attempts
        while not self.connected and max_attempts > 0:
            max_attempts -= 1
            self.logger.debug(f"host: attemppting to connect to CRUX, {max_attempts} attempts remaining...")
            before = time.time()
            try:
                async with timeout(self.timeout):
                    reader, writer = await asyncio.open_connection('127.0.0.1', 4005)
            except (ConnectionRefusedError, asyncio.TimeoutError) as err:
                self.logger.debug(f"host: can't connect to CRUX, {err!r}")
                # Asynchronously sleeps.  If `timeout` is set to 1 and
                # connection has failed in 0.5 second, sleep 0.5 second again.
                remaining = max(0, self.timeout - (time.time() - before))
                await asyncio.sleep(remaining)
                continue
            except asyncio.CancelledError:
                return
            except Exception:
                raise
            else:
                self.logger.debug("host: connected to CRUX.")
                self.connected = True
                self.writer = writer
                self.reader = reader

        if self.connected:
            await self.call_hook("connected", writer)
            self.reading_task = asyncio.create_task(self.read_commands(self.reader))
        else:
            await self.call_hook("cannot_connect")

    async def error_read(self, reader):
        """An error occurred when trying to read from CRUX."""
        if reader is self.reader:
            self.connected = False
            self.reader = None
            self.writer = None
            await self.parent.error_read()

    async def error_write(self, writer):
        """An error occurred when trying to read from CRUX."""
        if writer is self.writer:
            self.connected = False
            self.reader = None
            self.writer = None
            await self.parent.error_write()
