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

"""Blueprint document for exits."""

from data.base import db
from data.blueprints.document import Document
from data.blueprints.exceptions import DelayMe

class ExitDocument(Document):

    """Exit document to add exits in blueprints."""

    doc_type = "exit"
    doc_dump = False
    fields = {
        "name": {
            "type": "str",
            "max_len": 32,
            "presence": "required",
        },
        "back": {
            "type": "str",
            "max_len": 32,
            "presence": "optional",
        },
        "origin": {
            "type": "str",
            "presence": "required",
        },
        "destination": {
            "type": "str",
            "presence": "required",
        },
        "barcode": {
            "type": "str",
            "max_len": 32,
            "presence": "optional",
        },
    }

    def apply(self):
        """Apply the document, create an exit."""
        origin = db.Room.get(barcode=self.cleaned.origin)
        destination = db.Room.get(barcode=self.cleaned.destination)
        if origin is None or destination is None:
            raise DelayMe

        # If the exit already exists
        exit = db.Exit.between(origin, destination)
        if exit:
            # If there's no back name, might create a one-way exit.
            if not self.cleaned.back:
                exit.origin = origin
                exit.to = destination
                exit.name = self.cleaned.name
                exit.back = ""
            else:
                if exit.origin is origin:
                    name = self.cleaned.name
                    back = self.cleaned.back
                else:
                    name = self.cleaned.back
                    back = self.cleaned.name
                exit.name = name
                exit.back = back
            exit.barcode = self.cleaned.barcode
        else:
            exit = db.Exit(name=self.cleaned.name, back=self.cleaned.back,
                    origin=origin, to=destination,
                    barcode=self.cleaned.barcode)

        self.objects = (exit, )
