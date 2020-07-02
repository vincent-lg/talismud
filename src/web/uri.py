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

"""URI, connecting a page and optional programs."""

from importlib import import_module
from pathlib import Path

from Cheetah.Template import Template
from aiohttp import web

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

    async def process(self, request):
        """Process the current URI."""
        # Execute the program, if any
        program = self.methods.get(request.method.lower())
        print(f"{request.method} {self.uri}, {program}")
        if program:
            result = await program(request)

        self.page.messages = []
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

        Returns:
            uris (list): list of URIs.

        """
        uris = {}
        # First, gather the programs
        programs_path = Path() / "web/progs"
        for program_path in programs_path.rglob("*.py"):
            uri = program_path.relative_to(programs_path).as_posix()[:-3]
            pypath = program_path.as_posix()[:-3].replace("/", ".")
            program = import_module(pypath)

            # Create an URI object
            resource = URI("/" + uri)
            resource.program = program

            # Assign methods based on callable names
            print(f"load {pypath}")
            for key, value in program.__dict__.items():
                if key.startswith("_"):
                    continue

                if not callable(value):
                    continue

                if key not in ("get", "post", "put", "delete"):
                    continue

                resource.methods[key] = value
            uris[resource.uri] = resource

        # Gather the pages
        pages_path = Path() / "web/pages"
        for page_path in pages_path.rglob("*.tmpl"):
            with page_path.open("r", encoding="utf-8") as file:
                content = file.read()

            template = Template(content)
            uri = page_path.relative_to(pages_path).as_posix()[:-5]
            parts = uri.split("/")
            if parts[-1] == "index":
                uri = "/".join(parts[:-1])
            uri = f"/{uri}"
            resource = uris.get(uri)
            if resource is None:
                resource = URI(uri)
                uris[uri] = resource
            resource.page = template

        return uris
