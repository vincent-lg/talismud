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

"""Builder window, to create content in a graphical user interface."""

from pathlib import Path
import traceback

from bui import Window

from data.blueprints.blueprint import Blueprint as Blueprint
from data.blueprints.exceptions import BlueprintAlert
from data.blueprints.parser.yaml import YAMLParser
from service.launcher import MUDOp, MUDStatus
import settings
from ui.room import EditRoom

class BuilderWindow(Window):

    """Builder window, to create content in an interface."""

    def on_init(self):
        """The window is ready to be displayed."""
        self["map"].value = "Not set yet"
        self.map_size = 10 # 10 in radius, that is 21/21
        self.map_scale = 1 # how many rooms on one character
        self.map_center = [0, 0, 0]
        self.parser = YAMLParser(directory=settings.BLUEPRINT_DIRECTORY)

    def on_init_blueprints(self, widget):
        """The table is created."""
        self.parser.retrieve_blueprints()
        first_path = first_blueprint = None
        for path, blueprint in self.parser.blueprints.items():
            widget.add_row(path.stem, "Sometime", "No")
            if first_path is None:
                first_path = path
                first_blueprint = blueprint

        if widget.rows:
            first = widget.rows[0]
            widget.selected = first
            self.blueprint = first_blueprint
            self.update_map()

    def on_new(self):
        """Create a blueprint."""
        dialog = self.pop_dialog("""
            <dialog title="New blueprint">
              <text x=1 y=2 id=name>Blueprint name:</text>
              <text x=1 y=3 id=author>Who created this blueprint?</text>
              <button x=5 y=2 set_true>OK</button>
              <button x=5 y=4 set_false>Cancel</button>
            </dialog>
        """)

        if dialog:
            name = dialog["name"].value
            author = dialog["author"].value

    def on_save(self):
        """The user asks to save this blueprint."""
        print("Saving the current blueprint.")
        self.parser.store_blueprint(self.blueprint)

    def on_press_return_in_blueprints(self, widget):
        """The user presses RETURN while the list is focused."""
        pass

    def on_press_left_in_map(self, control):
        """Press the left arrow in the map."""
        self.map_center[0] -= 1
        self.update_map()
        control.stop()

    def on_press_right_in_map(self, control):
        """Press the left arrow in the map."""
        self.map_center[0] += 1
        self.update_map()
        control.stop()

    def on_press_down_in_map(self, control):
        """Press the left arrow in the map."""
        self.map_center[1] -= 1
        self.update_map()
        control.stop()

    def on_press_up_in_map(self, control):
        """Press the left arrow in the map."""
        self.map_center[1] += 1
        self.update_map()
        control.stop()

    def on_press_return_in_map(self):
        """The user presses RETURN while on the map."""
        room = self.blueprint.coords.get(tuple(self.map_center))
        if room:
            self.edit_room(room)

    def add_neighbor(self, control, key):
        """The users presses CTRL + Left arrow in the map."""
        x, y, z = self.map_center
        directions = {
            # key: (exit_to, exit_from)
            "ctrl_left": ("west", "east", x - 1, y, z),
            "ctrl_right": ("east", "west", x + 1, y, z),
            "ctrl_down": ("south", "north", x, y - 1, z),
            "ctrl_up": ("north", "south", x, y + 1, z),
        }

        # Creating a new room and exit leading in this direction
        exit_to, exit_from, x, y, z = directions[key]
        if (x, y, z) in self.blueprint.coords:
            self.pop_alert("Error",
                    f"There already is a room in X={x}, Y={y}, Z={z}.")
            return

        room = self.blueprint.coords[tuple(self.map_center)]
        if [exit for exit in room.cleaned.exits if
                exit.cleaned.name == exit_to]:
            self.pop_alert("Error",
                    f"The current room {room.cleaned.barcode} already "
                    f"has an exit leading toward {exit_to}."
            )
            return

        dialog = self.pop_dialog(EditRoom, room=None,
                blueprint=self.blueprint)
        if dialog:
            try:
                new_room = room.add_neighbor(barcode=dialog["barcode"].value,
                        title=dialog["title"].value, x=x, y=y, z=z,
                        description=dialog["description"].value,
                        exit_to=exit_to, exit_from=exit_from)
            except BlueprintAlert as err:
                self.pop_alert("Error", str(err))
            else:
                self.update_map()
                control.stop()
    on_press_ctrl_left_in_map = add_neighbor
    on_press_ctrl_right_in_map = add_neighbor
    on_press_ctrl_down_in_map = add_neighbor
    on_press_ctrl_up_in_map = add_neighbor

    def update_map(self):
        """Update the map according to the specified file."""
        coords = self.blueprint.coords
        current_map = ""
        min_x = self.map_center[0] - self.map_size - 1
        min_y = self.map_center[1] + self.map_size + 1
        max_x = self.map_center[0] + self.map_size + 1
        max_y = self.map_center[1] - self.map_size - 1
        z = self.map_center[2]

        for y in range(min_y, max_y + 1, -1):
            if current_map:
                current_map += "\n"

            for x in range(min_x, max_x + 1):
                cell = " "
                room = coords.get((x, y, z))
                if room:
                    cell = "#"

                current_map += cell

        self["map"].value = current_map
        self["map"].cursor.move(self.map_size + 1, self.map_size + 1)
        cursor = self["map"].cursor

    def edit_room(self, document):
        """Edit te given room."""
        with document.cleaned as room:
            dialog = self.pop_dialog(EditRoom, room=room,
                    blueprint=self.blueprint)
            if dialog:
                print(dialog["title"].value)
