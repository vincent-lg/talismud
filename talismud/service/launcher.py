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

"""Launcher service."""

import asyncio

from async_timeout import timeout as async_timeout

from service.base import BaseService

class Service(BaseService):

    """Launcher main service."""

    name = "launcher"
    sub_services = ("host", )

    async def init(self):
        """
        Asynchronously initialize the service.

        This method should be overridden in subclasses.  It is called by
        `start`` before sub-services are created.  It plays the role of
        an asynchronous constructor for the service, and service attributes
        often are created there for consistency.

        """
        self.has_admin = True

    async def setup(self):
        """Set the game up."""
        self.services["host"].connect_on_startup = False

    async def cleanup(self):
        """Clean the service up before shutting down."""
        pass

    async def error_read(self):
        """Cannot read from CRUX anymore, prepare to shut down."""
        pass

    # Command handlers
    async def handle_registered_game(self, reader, game_id, sessions, **kwargs):
        """The game service has been registered by CRUX."""
        pass

    async def handle_game_id(self, reader, game_id):
        """A game ID has been sent by the portal, do nothing."""
        pass

    async def handle_game_stopped(self, reader):
        """The game service has been registered by CRUX."""
        pass

    async def handle_created_admin(self, reader, success: bool):
        """
        When the portal receives 'created_admin', do nothing.

        This response is expected from the 'create_admin' handler.
        Intercepting this response while 'create_admin' hasn't been
        sent isn't of much use.

        """
        pass

    # User actions
    async def action_start(self) -> bool:
        """
        Start the game.

        Return whether the game was correctly started.

        Order of operations:
            1.  Connect to CRUX.  It should not work, since the portal
                shouldn't be running.  If it works, however, skip to step 4.
            2.  Launch the `poral` process.  This should also create a
                CRUX server.
            3.  Attempt to connect to CRUX again.  This time it should work,
                possibly after some retries.  If it doesn't, the start
                process is broken, report and stop.
            4.  Start the `game` process.  The game will attempt to
                connect to the portal and send a command to it to register.
            5.  On receiving the 'register_game' command, the portal will
                check that no other game has been registered, assign an
                ID for clarity to it, send the 'registered_game' command
                with the new game ID to all hosts.  This includes the
                launcher at this point.
            6.  Wait for the `registered_game` command to be issued.  If it
                is, report success to the user.

        """
        # 1. Connect to CRUX.  Failure is expected.
        host = self.services["host"]
        host.max_attempts = 2
        host.timeout = 0.2
        await host.connect_to_CRUX()

        if not host.connected:
            # 2. 'host' is not connected.  Start the portal.
            self.logger.info("Starting the portal ...")
            self.process.start_process("portal")

            # 3. Try to connect to CRUX again.  This time if it fails, it's an error.
            host.max_attempts = 20
            host.timeout = 1
            await host.connect_to_CRUX()

            if not host.connected:
                self.logger.error(
                        "The portal should have been started. For some "
                        "reason, it hasn't. Check the logs in "
                        "logs/portal.log for errors."
                )
                return False

            # The portal has started
            self.logger.info("... portal started.")
        else:
            self.logger.info("The portal is already running.")

        # 4. Start the game process
        self.logger.info("Starting the game ...")
        await host.send_cmd(host.writer, "start_game")

        # 5. The game process will send a 'register_game' command to CRUX.
        # 6. ... so wait for the 'registered_game' command to be received.
        success, args = await host.wait_for_cmd(host.reader, "registered_game",
                timeout=10)
        if success:
            game_id = args.get("game_id", "UNKNOWN")
            pid = args.get("pid", "UNKNOWN")
            self.has_admin = has_admin = args.get("has_admin", False)
            self.logger.info(f"... game started (id={game_id}, pid={pid}, has_admin={has_admin}).")
            return True
        else:
            self.logger.error(
                    "The game hasn't started. See logs/game.log "
                    "for more information."
            )
            return False

    async def action_stop(self):
        """
        Stop the game and portal process.

        Order of operations:
            1.  Connect to CRUX.  It should succeed.
            2.  Send the 'stop_portal' command to CRUX.
            3.  CRUX will send a 'stop_game' command to the game host.
            4.  Wait for CRUX to shut down.

        """
        # 1. Connect to CRUX.  Success is expected.
        host = self.services["host"]
        host.max_attempts = 10
        host.timeout = 2
        await host.connect_to_CRUX()

        if not host.connected:
            self.logger.warning("The portal seems to be off, the game isn't running.")
            return

        # 3. Send the 'stop_portal' command
        self.logger.info("Portal and game stopping ...")
        await host.send_cmd(host.writer, "stop_portal")

        # 4. Wait for any command to be received.  None should.
        await host.wait_for_cmd(host.reader, "*", timeout=10)
        if host.connected:
            self.logger.error("The portal is still running, although asked to shudown.")
        else:
            self.logger.info("... portal and game stopped.")

    async def action_restart(self):
        """
        Restart the game, maintains the portal.

        Order of operations:
            1.  Connect to CRUX.  It should succeed.
            2.  Send the 'stop_game' command to CRUX.
            3.  CRUX will send a 'restart_game' command to the game host.
            3.  Listen for the `stopped_game` command, that will
                be sent when the game has disconnected.
            4.  The portal will start the `game` process.  The game will
                attempt to connect to the portal and send a command to it
                to register.
            5.  On receiving the 'register_game' command, the portal will
                check that no other game has been registered, assign an
                ID for clarity to it, send the 'registered_game' command
                with the new game ID to all hosts.  This includes the
                launcher at this point.
            6.  Wait for the `registered_game` command to be issued.  If it
                is, report success to the user.

        """
        # 1. Connect to CRUX.  Success is expected.
        host = self.services["host"]
        host.max_attempts = 10
        host.timeout = 2
        await host.connect_to_CRUX()

        if not host.connected:
            self.logger.warning("The portal seems to be off, the game isn't running.")
            return

        # 2. Send the 'restart_game' command
        self.logger.info("Hame stopping ...")
        await host.send_cmd(host.writer, "restart_game", dict(announce=True))

        # 3. The portal should stop the game process...
        # ... and restart it.
        # 4. Listen for the 'stopped_game' command.
        success, args = await host.wait_for_cmd(host.reader, "game_stopped",
                timeout=10)
        if not success:
            self.logger.warning("The game is still running.")
            return

        self.logger.info("... game stopped.")
        self.logger.info("Start game ...")
        # 5. The game process will send a 'register_game' command to CRUX.
        # 6. ... so wait for the 'registered_game' command to be received.
        success, args = await host.wait_for_cmd(host.reader, "registered_game",
                timeout=10)
        if success:
            game_id = args.get("game_id", "UNKNOWN")
            self.logger.info(f"... game started (id={game_id}).")
        else:
            self.logger.error(
                    "The game hasn't started. See logs/game.log "
                    "for more information."
            )

    async def action_create_admin(self, username: str,
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
        host = self.services["host"]
        if host.writer:
            await host.send_cmd(host.writer, "create_admin",
                    dict(username=username, password=password, email=email))

        success, args = await host.wait_for_cmd(host.reader,
                "created_admin", timeout=60)
        return success
