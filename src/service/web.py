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

import asyncio
import base64
from pathlib import Path

from aiohttp import web as aioweb
from aiohttp_session import setup, get_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from cryptography import fernet

from service.base import BaseService
import settings
from web.base_template import BaseTemplate
from web.session import PonyStorage
from web.uri import URI

class Service(BaseService):

    """Web service."""

    name = "web"
    sub_services = ()

    async def init(self):
        """
        Asynchronously initialize the service.

        Setup the service information to run the web server asynchronously.

        """
        self.base_tamplates = {}
        self.preparing_task = None
        self.app = aioweb.Application()
        self.runner = aioweb.AppRunner(self.app)

    async def setup(self):
        """
        Set the web service up.

        Prepare to start the server, load base templates.

        """
        self.load_base_templates()
        uris = URI.gather()
        for uri, resource in uris.items():
            methods = resource.methods
            if "get" not in methods:
                methods["get"] = None

            for method in methods.keys():
                print(f"Add {method} for {resource.uri}")
                self.app.add_routes([
                        getattr(aioweb, method)(uri, resource.process)
                ])
        self.app.add_routes([aioweb.get("/hello", hello)])

        # TMP code
        max_age = 3600 * 24 * 365 # 1 year
        setup(self.app, PonyStorage(max_age=max_age))
        self.preparing_task = asyncio.create_task(self.prepare_web())

    async def cleanup(self):
        """Clean the service up before shutting down."""
        if self.preparing_task:
            self.preparing_task.cancel()

    async def prepare_web(self):
        """Start to serve asynchronously."""
        try:
            await self.serve_web()
        except asyncio.CancelledError:
            pass
        except Exception:
            self.logger.exception("web: an error occurred while serving:")

    async def serve_web(self):
        """Asynchronously start the web server."""
        interface = "0.0.0.0" if settings.PUBLIC_ACCESS else "127.0.0.1"
        port = settings.WEB_PORT
        self.logger.info(f"web: starting the server on {interface}:{port}...")
        await self.runner.setup()
        site = aioweb.TCPSite(self.runner, interface, port)
        await site.start()
        self.preparing_task = None

    def load_base_templates(self):
        """
        Synchronously load the base templates.

        Contrary to page templates, base templates are loaded with the server.  Page templates will be loaded when a requests asks for them.

        """
        path = Path("web/bases")

        # Base templates are in web/pages and have the .tmpl extension
        for base_path in path.rglob("*.tmpl"):
            relative = base_path.relative_to(path)
            identifier = relative.as_posix().replace("/", ".")[:-5]
            with base_path.open("r", encoding="utf-8") as file:
                content = file.read()
            template = BaseTemplate.compile(content, moduleName=identifier,
                    baseclass=BaseTemplate)
            print(f"Loading base template {identifier}.")


async def hello(request):
    session = await get_session(request)
    num = session["num"] if "num" in session else 0
    num += 1
    session["num"] = num
    return aioweb.Response(text=f"Hello, <b>for your {num} visit</b>!", content_type="text/html")
