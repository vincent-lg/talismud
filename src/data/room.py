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

"""Room entity."""

import asyncio

from pony.orm import Optional, PrimaryKey, Required, Set

from data.base import db, PicklableEntity
from data.decorators import lazy_property
from data.group import group_names
from data.exit import ExitHandler
from data.handlers import (
        AttributeHandler, BlueprintHandler, DescriptionHandler,
        LocatorHandler)

class Room(PicklableEntity, db.Entity):

    """Room entity."""

    title = Required(str, max_len=128)
    x = Optional(int)
    y = Optional(int)
    z = Optional(int)
    barcode = Required(str, max_len=32, unique=True, index=True)
    exits_from = Set("Exit", reverse="origin")
    exits_to = Set("Exit", reverse="to")
    repop = Set("RoomRepop", reverse="room")
    has_spawned = Set("NPC", reverse="origin")

    @lazy_property
    def db(self):
        return AttributeHandler(self)

    @lazy_property
    def blueprints(self):
        return BlueprintHandler(self)

    @lazy_property
    def exits(self):
        """Return the ExitHandler."""
        return ExitHandler(self)

    @lazy_property
    def description(self):
        return DescriptionHandler(self)

    @lazy_property
    def locator(self):
        return LocatorHandler(self)

    @lazy_property
    def location(self):
        return self.locator.get()

    @location.setter
    def location(self, new_location):
        self.locator.set(new_location)

    @property
    def contents(self):
        return self.locator.contents()

    @property
    def characters(self):
        """Return a list of characters in this room."""
        return [content for content in self.contents
                if isinstance(content, db.Character)]

    # Database hooks
    def after_update(self):
        """Save in the room blueprints, if any."""
        loop = asyncio.get_event_loop()
        loop.call_soon(self.blueprints.save)

    def force_repop(self):
        """Force the current room to repop."""
        for line in self.repop:
            # Get all NPCs of that prototype whose origin is self.
            already = db.NPC.select(lambda NPC: NPC.origin == self
                    and NPC.prototype == line.prototype).count()
            to_pop = line.number - already
            if to_pop > 0:
                for _ in range(to_pop):
                    line.prototype.create_at(self)

    def look(self, character: 'db.Character'):
        """
        The character wants to look at this room.

        Args:
            character (Character): who looks at this room.

        """
        description = self.description and self.description.format() or ""
        exits = self.exits.all()
        if exits:
            exits = "Obvious exits: " + ", ".join([ex.name_for(self) for ex in exits])
        else:
            exits = "There is no obvious exit."

        lines = [
            self.title,
            "",
            description,
            "",
            exits,
        ]

        # Add the present characters
        characters = self.characters
        characters = [char for char in characters if char is not character]
        if characters:
            names = group_names(characters, character)
            names = [f"- {name}" for name in names]
            lines.append("")
            lines.extend(names)

        # Return the full room description.
        return "\n".join(lines)


class RoomRepop(PicklableEntity, db.Entity):

    """A line of repop, linking a room, character prototypes and number."""

    room = Required("Room", reverse="repop")
    prototype = Required("CharacterPrototype", reverse="repop")
    PrimaryKey(room, prototype)
    number = Required(int)
