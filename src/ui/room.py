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

"""Room dialog, to add or edit rooms."""

from bui.widget.dialog import Dialog

from ui.exit import EditExit

class EditRoom(Dialog):

    """Edit or create a room."""

    def on_init(self):
        if self.room:
            self.title = f"Editing {self.room.title}"
            self["barcode"].value = self.room.barcode
            self["title"].value = self.room.title
            self["description"].value = self.room.description

            # Fill in the exits
            self.update_exits()
            self["barcode"].disable()
        else:
            self.title = "Room creation"

    def update_exits(self, select=None):
        """Update the exit tables."""
        if self.room.exits:
            table = self["exits"]
            table.rows = []
            select_index = 0
            for i, document in enumerate(self.room.exits):
                with document.cleaned as exit:
                    dest = exit.destination
                    dest = self.blueprint.rooms.get(dest)
                    if dest:
                        dest = dest.cleaned.title
                    else:
                        dest = "Unknown destination"
                    back = (f"yes (toward {exit.back})" if
                            exit.back else "no")
                    table.add_row(exit.name, dest, back)
                    if select and exit.name == select:
                        select_index = i

            table.selected = select_index

    def on_remove_exit(self, control):
        """The user wants to remove this exit."""
        exits = self["exits"]
        exits.remove_row(exits.selected)

    def on_add_exit(self):
        """The user wants to add an exit."""
        dialog = self.pop_dialog(EditExit, room=self.room, exit=None,
                blueprint=self.blueprint)
        if dialog:
            name = dialog["name"].value
            destination = dialog["destination"].value
            back = dialog["back"].value
            new_exit = self.blueprint.create_document({
                    "type": "exit",
                    "name": name,
                    "back": back,
                    "origin": self.room.barcode,
                    "destination": destination,
            })
            self.room.exits.append(new_exit)

            # If it's a two-way exit, create the back exit in the destination
            if back:
                destination = self.blueprint.rooms[destination]
                back_exits = [exit for exit in destination.cleaned.exits
                        if exit.cleaned.name == back or
                        exit.cleaned.destination == self.room.barcode]

                if not back_exits:
                    back_exit = self.blueprint.create_document({
                        "type": "exit",
                        "name": back,
                        "back": name,
                        "origin": destination,
                        "destination": self.room.barcode,
                    })
                    destination.cleaned.exits.append(back_exit)

            # In any case, update the exit list
            self.update_exits(name)
