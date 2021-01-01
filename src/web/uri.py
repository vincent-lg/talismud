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

"""URI, connecting a page and optional programs."""

import inspect
from pathlib import Path
import types

from aiohttp import web
from aiohttp_session import get_session
from Cheetah.Template import Template

import settings

class URI:

    """URI, object to connect a page and optional programs.

    A prgram is a Python callable which is linked to a URI.  The page
    is a template that matches this URI.  A page can exist without a
    program.  A program can exist without a page.  If neither page nor
    program can be found at this URI, a 404 error is raised.

    Prgrams and pages can apply to a specific method of an URI.  For
    instance, if the user wishes to access the URI /about, it is possible
    to have different programs (and pages) depending on whether the
    request asked for a GET or POST method.

    """

    def __init__(self, uri):
        self.uri = uri
        self.program = None
        self.page = None
        self.methods = {}

        # Additional information (not required)
        self.template_path = None
        self.program_path = None

    async def process(self, request):
        """Process the current URI."""
        # Execute the program, if any
        program, signature = self.methods.get(request.method.lower(),
                (None, None))
        self.page.messages = []
        if program:
            # Dynamically build keyword arguments
            parameters = tuple(signature.parameters.keys())
            kwargs = {}
            for key, value in request.match_info.items():
                if key in parameters:
                    kwargs[key] = value

            if "request" in parameters:
                kwargs["request"] = request

            if "page" in parameters:
                kwargs["page"] = self.page

            if "session" in parameters:
                kwargs["session"] = await get_session(request)

            result = await program(**kwargs)

        response = str(self.page)
        return web.Response(text=response, content_type="text/html")

    @staticmethod
    def gather():
        """
        Gather programs and pages, creating URIs.

        Programs are stored in web/programs with a .py extension.  A program
        module should contain the method names as callable (get, post,
        put...).

        Pages can be found in web/pages with the .tmpl extension.  Pages
        can apply to all methods if they don't specify it in their file
        name.  For instance, a file called get.tmpl in web/pages/about/
        will be linked to the URI /about and the method GET.
        However, a file ccalled about.tmpl in web/pages/ will be
        linked to the URI /about, no matter the method.

        Additionally, this method will also dynamically load plugin
        programs and pages.

        Returns:
            uris (list): list of URIs.

        """
        uris = {}

        # First, gather the programs
        web_paths = [Path() / "web"]
        plugins_path = Path() / "plugins"
        web_paths += [plugins_path / name / "web" for name in settings.PLUGINS]

        for web_path in web_paths:
            programs_path = web_path / "progs"
            for program_path in programs_path.rglob("*.py"):
                uri = program_path.relative_to(programs_path).as_posix()[:-3]

                # Read the module and execute it, instead of importing it
                # This is due to the fact that the path might not be
                # valid Python.
                with program_path.open("r", encoding="utf-8") as file:
                    content = file.read()

                program = types.ModuleType(uri)
                exec(content, program.__dict__)

                # Create an URI object
                uri = URI.parse_uri(uri)
                resource = URI("/" + uri)
                resource.program = program
                resource.program_path = program_path.relative_to(web_path)

                # Assign methods based on callable names
                for key, value in program.__dict__.items():
                    if key.startswith("_"):
                        continue

                    if not callable(value):
                        continue

                    if key not in ("get", "post", "put", "delete"):
                        continue

                    signature = inspect.signature(value)
                    resource.methods[key] = (value, signature)
                uris[resource.uri] = resource

            # Gather the pages
            pages_path = web_path / "pages"
            for page_path in pages_path.rglob("*.tmpl"):
                with page_path.open("r", encoding="utf-8") as file:
                    content = file.read()

                template = Template(content)
                uri = page_path.relative_to(pages_path).as_posix()[:-5]
                uri = "/" + URI.parse_uri(uri)
                if uri.endswith("/index"):
                    uri = uri[:-5]
                resource = uris.get(uri)
                if resource is None:
                    resource = URI(uri)
                    uris[uri] = resource
                resource.page = template
                resource.page_path = page_path.relative_to(web_path)

        return uris

    @staticmethod
    def parse_uri(uri: str) -> str:
        """Parse the URI, returning an URI valid for the router."""
        parts = uri.split("/")

        for i, part in enumerate(parts):
            if part.startswith("$"):
                parts[i] = f"{{{part[1:]}}}"

        uri = "/".join(parts)
        return uri
