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

"""Room entity."""

from pony.orm import Optional, Required, Set

from data.base import db, PicklableEntity
from data.decorators import lazy_property
from data.exit import ExitHandler
from data.handlers import AttributeHandler, DescriptionHandler, LocatorHandler

class Room(PicklableEntity, db.Entity):

    """Room entity."""

    title = Required(str, max_len=128)
    x = Optional(int)
    y = Optional(int)
    z = Optional(int)
    barcode = Required(str, max_len=32, unique=True, index=True)
    exits_from = Set("Exit", reverse="origin")
    exits_to = Set("Exit", reverse="to")

    @lazy_property
    def db(self):
        return AttributeHandler(self)

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
            exits = "Obvious exits: well, none"

        lines = [
            self.title,
            "",
            description,
            "",
            exits,
            "HP: 100",
        ]

        return "\n".join(lines)
