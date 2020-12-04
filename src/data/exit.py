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

"""Exit entity, to connect rooms bidirectionally."""

import typing as ty

from pony.orm import Optional, Required, Set

from data.base import db, PicklableEntity
from data.decorators import lazy_property
from data.handlers import BlueprintHandler

class Exit(PicklableEntity, db.Entity):

    """
    Exit entity, to connect two rooms.

    Exits are bidirectional by default.  The following entity can
    be understood in two directions.  Assuming you want to
    connect room A to room B, then:

    1.  Room A -> Exit(name) -> Room B.
    2.  Room B -> Exit(back) -> Room A.

    In other words, an exit connects one room to another, and this
    other room to the original room as well.  The exit name from origin
    to destination is stored in `name`, the name of the exit
    connecting destination to origin is stored in `back`.  The
    `back` attribute can be removed, effectively creating a one-way
    exit with no back exit.

    Although more complex than a simple one-way exit system,
    this has the advantage of avoiding to multiply exit objects in
    the database to connect every room.  Obviously, if you want
    to create a game with few back exits, you might want to edit
    this entity to revert to a one-way exit system.

    Fields:
        name (str): the exit name or direction (like "east").
        back (str, optional): the exit back name (like "west").
        origin (Room, optional): the origin room.
        to (Room, optional): the destination room.
        barcode (str, optional): a str identifier for this exit.

    Notice that an exit can exist with no origin and/or destination
    room.  This would create a "floating exit", still stored in
    the database but connecting nothing to nothing.  However, such a
    floating exit should always have a barcode to retrieve it later.
    The use case for such floating exits would be vehicles that can
    be "closed" while on the move (their exit will be removed) but that
    should have an exit when they stop.  Rather than creating
    a different Exit object each time the vehicle stops,
    it is more efficient to assign the vehicle exit a unique
    barcode and keep the same exit object in the database
    for a single vehicle.

    """

    name = Required(str, max_len=32)
    back = Optional(str, max_len=32)
    origin = Optional("Room", reverse="exits_from")
    to = Optional("Room", reverse="exits_to")
    barcode = Optional(str, max_len=32)

    @lazy_property
    def blueprints(self):
        return BlueprintHandler(self)

    def name_for(self, room):
        """
        Return the exit name for this room.

        The exit name will vary: if the given room is the origin, return
        `name`.  If the given room is `to`, return `back`.  Otherwise,
        raise a Valueerror exception.

        Args:
            room (Room): the origin or destination room for this exit.

        """
        if self.origin is room:
            return self.name
        elif self.to is room:
            return self.back

        raise ValueError(
                f"{room} is neither origin not destination of this exit"
        )

    def destination_for(self, room):
        """Return the destination for the given room."""
        if self.origin is room:
            return self.to
        elif self.to is room:
            return self.origin

        raise ValueError(f"{room} is neither origin not destination here")

    @classmethod
    def of(cls, room):
        """
        Return the exits of the specified room.

        Args:
            room (Room): the exits of this room.

        Note:
            Since exits can have two directions, this method can
            be used (often as a shortcut, prefer using the
            ExitHandler in `room.exits`) to retrieve a set of exits
            that would have origin or to set to the given room,
            assuming there's an active back exit.


        """
        return cls.select(lambda exit: exit.origin is room or (
                exit.to is room and exit.back)
        )

    @classmethod
    def between(cls, origin, destination):
        """Return the exit between origin and destination, or None."""
        exits = list(cls.select(lambda exit: (
                exit.origin is origin and exit.to is destination) or (
                exit.to is origin and exit.origin is destination)
        ))
        return exits[0] if exits else None


class ExitHandler:

    """Exit handler, to interact with room exits."""

    def __init__(self, room):
        self.room = room

    def __repr__(self):
        """Return the repr for the room exits."""
        exits = Exit.of(self.room)
        reprs = []
        for exit in exits:
            if exit.origin is self.room:
                reprs.append(f"<Exit({exit.name})>")
            else:
                reprs.append(f"<BackExit({exit.back})>")

        return repr(reprs)

    def all(self):
        """Return all exits."""
        return list(Exit.of(self.room))

    def match(self, character: db.Character, name: str) -> ty.Optional[Exit]:
        """
        Return whether the given match is an exit name.

        Args:
            character (Character): the character searching exits.
            name (str): the exit name.

        Returns:
            Exit or None: found or not found exit.

        """
        name = name.lower()
        for exit in Exit.of(self.room):
            if exit.name_for(self.room) == name:
                return exit

        return None # Explicit is better than implicit
