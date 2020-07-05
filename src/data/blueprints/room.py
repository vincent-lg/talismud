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

"""Blueprint document for rooms."""

from data.base import db
from data.blueprints.document import Document

class RoomDocument(Document):

    """Room document to add rooms in blueprints."""

    fields = {
        "barcode": {
            "type": "str",
            "max_len": 32,
            "presence": "required",
        },
        "title": {
            "type": "str",
            "max_len": 128,
            "presence": "required",
        },
        "x": {
            "type": "int",
            "presence": "optional",
        },
        "y": {
            "type": "int",
            "presence": "optional",
        },
        "z": {
            "type": "int",
            "presence": "optional",
        },
        "description": {
            "type": "str",
            "presence": "optional",
        },
    }

    def apply(self):
        """Apply the document, create a room."""
        room = db.Room.get(barcode=self.cleaned.barcode)
        if room is None:
            room = db.Room(barcode=self.cleaned.barcode,
                    title=self.cleaned.title)
            print(f"creating {room}")
        else:
            print(f"updating {room}")
            room.title = self.cleaned.title

        room.x = self.cleaned.x
        room.y = self.cleaned.y
        room.z = self.cleaned.z

        description = self.cleaned.description
        if description:
            if room.description:
                room.description.text = description
            else:
                room.description = db.RoomDescription(text=description)
