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

"""Exit dialog, to add or edit exits."""

from collections import deque

from bui.widget.dialog import Dialog

class EditExit(Dialog):

    """Edit or create an exit."""

    def on_init(self):
        if self.exit:
            self.title = (
                f"Editing exit {self.exit.name} in {self.room.title}"
            )
            self["name"].value = self.exit.name
            self["destination"].value = self.exit.destination
            self["back"].value = self.exit.back
        else:
            self.title = "Exit creation in {self.room.title}"

        # Suggestions
        self.suggested_begin = None
        self.suggested_list = None

    def on_ok(self, control):
        """When the OK button is clocked."""
        name = self["name"].value
        if not name:
            self.pop_alert(title="Error",
                    message="You have to specify a name.")
            control.stop()

        exits = {exit.cleaned.name: exit.cleaned for exit in self.room.exits}
        if name in exits:
            self.pop_alert(title="Error",
                    message=f"There already is an exit named {name} "
                    "in this room.")
            control.stop()

        # Check that the destination is valid
        dest = self["destination"].value
        if dest not in self.blueprint.rooms:
            self.pop_alert(title="Error",
                    message=f"There are no room of barcode {dest} "
                    "in this blueprint.")
            control.stop()

        if dest == self.room.barcode:
            self.pop_alert(title="Error",
                    message="This exit would point to the current room, "
                            "which is not accepted.")
            control.stop()

        # All is OK, do nothing

    def scroll_through_suggestions(self, widget, control, key):
        """Browse the list of suggestions."""
        rotation = -1 if key == "down" else 1
        self.update_suggestions()
        self.suggested_list.rotate(rotation)
        widget.value = self.suggested_list[0]
        widget.cursor.move(0)
        control.stop()
    on_press_down_in_destination = scroll_through_suggestions
    on_press_up_in_destination = scroll_through_suggestions

    def on_type_in_destination(self):
        """When the user types on her keyboard in the destination field."""
        self.suggested_list = None

    def update_suggestions(self):
        """Make sure suggestions exist."""
        if self.suggested_list is None:
            self.suggested_begin = self["destination"].value
            self.suggested_list = deque([room.cleaned.barcode for room in
                    self.blueprint.rooms.values()
                    if room.cleaned.barcode.startswith(self.suggested_begin)])
