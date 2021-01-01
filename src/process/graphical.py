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

"""The graphical launcher process, should control portal and game."""

import asyncio

from process.launcher import Launcher

try:
    from window import TalismudWindow
except ModuleNotFoundError:
    TalismudWindow = None

class Graphical(Launcher):

    """
    Graphical launcher process, running the launcher service.

    The launcher process should only have a connection to the CRUX server.
    This host service can be expected to be unavailable altogether.

    """

    name = "graphical"
    services = ("launcher", )

    def __init__(self):
        super().__init__()
        self.stream_handler.format_string = "{record.message}"
        self.window_task = None

    async def setup(self):
        """Called when services have all been started."""
        launcher = self.services["launcher"]
        if TalismudWindow is None:
            raise ValueError(
                "bui isn't installed, can't create the graphical launcher"
            )

        self.window = TalismudWindow.parse_layout(TalismudWindow, process=self, service=launcher)
        self.window_task = asyncio.create_task(self.start_window())

    async def cleanup(self):
        """Called when the process is about to be stopped."""
        if self.window_task:
            self.window_task.cancel()

    async def start_window(self):
        """Start the TalisMUD window."""
        loop = asyncio.get_event_loop()
        try:
            await self.window._start(loop)
        except asyncio.CancelledError:
            pass
        except Exception:
            self.logger.exception("An error occurred in the TalisMUD window:")
        finally:
            self.window._stop()
            self.window.close()
