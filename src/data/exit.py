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

"""Exit entity, to connect rooms bidirectionally."""

from enum import Enum, auto
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

    def back_for(self, room):
        """
        Return the exit's back name for this room.

        The exit back name will vary: if the given room is the origin, return
        `back`.  If the given room is `to`, return `name`.  Otherwise,
        raise a Valueerror exception.

        Args:
            room (Room): the origin or destination room for this exit.

        """
        if self.origin is room:
            return self.back
        elif self.to is room:
            return self.name

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

    def __iter__(self):
        return iter(tuple(Exit.of(self.room)))

    def all(self):
        """Return all exits."""
        return list(Exit.of(self.room))

    def has(self, name: str) -> bool:
        """
        Return whether the current room has an exit named like this.

        Args:
            name (str): name of the exit to check.

        The comparison is performed case-insensitive.

        Returns:
            exist (bool): whether an exit with this name exists.

        """
        name = name.lower()
        for exit in self:
            if exit.name == name:
                return True

        return False

    def link_to(self, destination: 'db.Room', name: str,
            back: ty.Optional[str] = None, barcode: ty.Optional[str] = "",
            ) -> ty.Optional['db.Exit']:
        """
        Link the owner room to the specified destination.

        Both rooms have to exist for this method to work.  Neither
        room should be connected, it would break the exit system
        if more than one exit linked two rooms.

        Args:
            destination (Room): the exit destination.
            name (str): the exit name.
            back (str, optional): the name of the back exit, if any.
            barcode (str, optional): the exit barcode, if any.

        Returns:
            exit (Exit or None): the exit if created, None if error.

        """
        origin = self.room
        if Exit.between(origin, destination):
            return

        # Create an exit connected origin to destination
        return db.Exit(origin=origin, to=destination,
                name=name, back=back, barcode=barcode)

    def create_room(self, direction: 'Direction', name: str,
            destination: str, title: str, back: ty.Optional[str] = None,
            barcode: ty.Optional[str] = "") -> 'db.Exit':
        """
        Create a room in the specified direction, linking it with an exit.

        This method is usually the one called to add rooms
        and exits with no real difficulty.  This would fail for several
        reasons, raise as a `NewRoomError` subclass.

        Args:
            direction (DIRECTION): a member of DIRECTION, like
                    DIRECTION.SOUTH or DIRECTION.UP.  This is
                    the exit direction and the name of the exit
                    is specified in the next argument.
            name (str): the exit name.
            destination (str): the destination's future barcode.
                    This will be the new room's barcode and thus,
                    shouldn't be used already.
            title (str): the new room's title.
            back (str, optional): the name of the exit
                    from destination to origin (the back exit).
                    If not set, don't create a back exit.
            barcode (str, optional): the exit's barcode, a way
                    to uniquely identify the exit.  It shouldn't be
                    used by another exit.

        Returns:
            exit (Exit): the newly-created exit, if successful.

        Raises:
            A subclass of `NewRoomError` to inform the user of several
            possible errors.  This should be intercepted (in a
            command, probably) and handled to display the error
            in a user-friendlier way.

            Possible errors:
                CoordinatesInUse(x, y, z, room): these coordinates are
                        in use, can't create the destination room.
                ExitNameInUse(room, name): this exit name is already
                        in use in this room, cannot create it.

        """
        origin = self.room
        x, y, z = origin.x, origin.y, origin.z

        # If the coordinates are valid, check the new coordinates
        if all(value is not None for value in (x, y, z)):
            x, y, z = direction.shift(x, y, z)

        # Check fthat the coordinates are free
        if (dest := db.Room.get(x=x, y=y, z=z)):
            raise CoordinatesInUse(x, y, z, dest)

        # Check whether there is no exit of this name yet
        if self.has(name):
            raise ExitNameInUse(room, name)

        # Create a room with these coordinates
        destination = db.Room(barcode=destination, title=title, x=x, y=y, z=z)

        # Copy the current blueprints to the new room
        for blueprint in origin.blueprints.get():
            destination.blueprints.add(blueprint.name)

        exit = self.link_to(destination, name=name, back=back,
                barcode=barcode)
        origin.blueprints.save(destination)
        return exit

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


class Direction(Enum):

    """Enumeration listing possible exit directions."""

    UNSET = auto()
    EAST = auto()
    SOUTHEAST = auto()
    SOUTH = auto()
    SOUTHWEST = auto()
    WEST = auto()
    NORTHWEST = auto()
    NORTH = auto()
    NORTHEAST = auto()
    DOWN = auto()
    UP = auto()

    def shift(self, x: int, y: int, z: int) -> ty.Tuple[int, int, int]:
        """
        Shift the coordinates according to the direction.

        Args:
            x (int): the original X cooridnates.
            y (int): the original Y coordinates.
            z (int): the original Z coordinates.

        Returns:
            x, y, z (int, int int): the shifted coordinates.

        Example:

            >>> x, y, z = 0, 0, 0
            >>> Direction.EAST.shift(x, y, z)
            (1, 0, 0) # x has shifted (x + 1)

        """
        if self is Direction.UNSET:
            raise ValueError("an unset exit direction cannot shift")
        elif self is Direction.EAST:
            x += 1
        elif self is Direction.SOUTHEAST:
            x += 1
            y -= 1
        elif self is Direction.SOUTH:
            y -= 1
        elif self is Direction.SOUTHWEST:
            x -= 1
            y -= 1
        elif self is Direction.WEST:
            x -= 1
        elif self is Direction.NORTHWEST:
            x -= 1
            y += 1
        elif self is Direction.NORTH:
            y += 1
        elif self is Direction.NORTHEAST:
            x += 1
            y += 1
        elif self is Direction.DOWN:
            z -= 1
        elif self is Direction.UP:
            z += 1
        else:
            raise ValueError("unknown exit direction")

        return x, y, z


class NewRoomError(Exception):

    """Parent exception for new room errors."""

    pass


class CoordinatesInUse(NewRoomError):

    """Exception raised when the coordinates already are in use."""

    def __init__(self, x, y, z, room):
        self.x = x
        self.y = y
        self.z = z
        self.room = room

    def __str__(self):
        return (f"coordinates X={self.x}, Y={self.y}, Z={self.z} "
                f"already are used by {self.room}")


class ExitNameInUse(NewRoomError):

    """The specified exit name already is in use."""

    def __init__(self, room, name):
        self.room = room
        self.name = name

    def __str__(self):
        return f"the exit {self.exit!r} already exists in {self.room}"
