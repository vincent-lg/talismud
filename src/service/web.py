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

"""Web service to run on the game process."""

from aiohttp import web as aioweb
import asyncio

from service.base import BaseService
import settings

class Service(BaseService):

    """Web service."""

    name = "web"
    sub_services = ()

    async def init(self):
        """
        Asynchronously initialize the service.

        This method should be overridden in subclasses.  It is called by
        `start`` before sub-services are created.  It plays the role of
        an asynchronous constructor for the service, and service attributes
        often are created there for consistency.

        """
        self.preparing_task = None
        self.app = aioweb.Application()
        self.app.add_routes([aioweb.get('/', hello)])
        self.runner = aioweb.AppRunner(self.app)

    async def setup(self):
        """Set the portal up."""
        self.preparing_task = asyncio.create_task(self.serve_web())

    async def cleanup(self):
        """Clean the service up before shutting down."""
        if self.preparing_task:
            self.preparing_task.cancel()

    async def serve_web(self):
        """Asynchronously start the web server."""
        interface = "0.0.0.0" if settings.PUBLIC_ACCESS else "127.0.0.1"
        port = settings.WEB_PORT
        self.logger.info(f"web: starting the server on {interface}:{port}...")
        try:
            await self.runner.setup()
            site = aioweb.TCPSite(self.runner, interface, port)
            await site.start()
        except asyncio.CancelledError:
            pass

        self.preparing_task = None


async def hello(request):
    return aioweb.Response(text="Hello, world")
