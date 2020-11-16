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

from typing import Optional

from data.base import db
from data.blueprints.document import Document
from data.blueprints.exceptions import BlueprintAlert, DelayMe, DelayDocument

class RoomDocument(Document):

    """Room document to add rooms in blueprints."""

    doc_type = "room"
    doc_dump = True
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
        "exits": {
            "type": "subset",
            "document_type": "exit",
        },
    }

    def add_neighbor(self, barcode: str, title: str, x: Optional[int] = None,
            y: Optional[int] = None, z: Optional[int] = None,
            description: Optional[str] = None,
            exit_to: Optional[str] = None, exit_from: Optional[str] = None):
        """
        Add a room, optionally connected to the current room.

        Args:
            barcode (str): the new room's barcode.
            title (str): the new room's title.
            x (int, optional): the X coordinate of the new room.
            z (int, optional): the Z coordinate of the new room.
            z (int, optional): the Z coordinate of the new room.
            description (str, optional): the new room's description.
            exit_to (str, optional): the name of the exit from
                    self to the new room.  If left to None, no exit
                    is created.
            exit_from (str, optional): the name of the exit from
                    the new room to self.  If left to None, no exit
                    is created.

        Returns:
            new_room (RoomDocument): the new room if successful.

        Raises:
            BlueprintAlert if something went wrong.

        """
        room = self.cleaned
        if (x, y, z) in self.blueprint.coords:
            raise BlueprintAlert(
                    f"There already is a room in X={x}, Y={y}, Z={z}."
            )

        if exit_to and [exit for exit in room.exits
                if exit.cleaned.name == exit_to]:
            raise BlueprintAlert(
                    f"The current room {room.barcode} already "
                    f"has an exit leading {exit_to}."
            )

        if barcode in self.blueprint.rooms:
            raise BlueprintAlert(f"the barcode {barcode} is already used")

        new_room = self.blueprint.create_document({
                "type": "room",
                "barcode": barcode,
                "x": x,
                "y": y,
                "z": z,
                "title": title,
                "description": description,
        })
        self.blueprint.documents.append(new_room)

        # Create the exit from room to new_room
        if exit_to:
            new_exit = self.blueprint.create_document({
                    "type": "exit",
                    "name": exit_to,
                    "back": exit_from,
                    "origin": room.barcode,
                    "destination": new_room.cleaned.barcode,
            })
            self.blueprint.documents.append(new_exit)
            room.exits.append(new_exit)

        # Create the back exit
        if exit_from:
            back_exit = self.blueprint.create_document({
                    "type": "exit",
                    "name": exit_from,
                    "back": exit_to,
                    "origin": new_room.cleaned.barcode,
                    "destination": room.barcode,
            })
            self.blueprint.documents.append(back_exit)
            new_room.cleaned.exits.append(back_exit)

    def apply(self):
        """Apply the document, create a room."""
        room = db.Room.get(barcode=self.cleaned.barcode)
        if room is None:
            room = db.Room(barcode=self.cleaned.barcode,
                    title=self.cleaned.title)
        else:
            room.title = self.cleaned.title

        room.x = self.cleaned.x
        room.y = self.cleaned.y
        room.z = self.cleaned.z

        description = self.cleaned.description
        if description:
            room.description.set(description)

        # Add the exits, if possible
        for exit in list(self.cleaned.exits):
            try:
                exit.apply()
            except DelayMe:
                self.cleaned.exits.remove(exit)
                raise DelayDocument(exit)
