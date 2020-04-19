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

"""Mixint to add location to an entity."""

from itertools import count

from pony.orm import commit, select, Optional, OrmError, Required

from data.base import db
from data.properties import lazy_property

class HasLocation:

    """
    Mixin to add the notion of location (and contents) to an entity.

    An entity can store a location to a remote entity.  For instance,
    a character in game can have a location in its current room
    entity.  The code to get or set locations in the character is
    extremely simple:

    >>> character.location # Get the character's location or None
    Room(Beginning)
    >>> character.location = new_location

    Changing location to itself or to create a loop (A would contain B
    which counains A...) is not allowed.  Checking this might generate
    a lot of queries.  It is unlikely you will need more than 5 or 7 depth
    of contents, but TalisMUD doesn't restrict you.  Just know that there's
    a performance cost to do so.

    Since each object can have a location, it also has a contents.
    The object contents is a list describing all the entities that
    have their location set to this object.  For instance:

    >>> room = Room[1] # Get the room of ID 1
    >>> character = Character[3] # Get the character of ID 3
    >>> character.location = room # Move the character in the room
    >>> room.contents
    [Character[3]]
    >>> character2 = Character[32] # Character of ID 32
    >>> character.location = room
    >>> room.contents
    [Character[3], Character[32]]

    Note: the order of the content list is maintained.  If you add
    `obj1` in a location, then `obj2` in the same location, the
    location's `contents` will be `[obj1, obj2]`.  Each time an object
    is moved, a "position index" is added (`obj1` will get 1,
    `obj2` will get 2, and so on).  When the contents is returned,
    the list is sorted by location index.

    """

    @staticmethod
    def extend_entity(cls):
        """Add entity attributes to the entity."""
        cls.location_entity = Optional(str, max_len=32)
        cls.location_pkey = Optional(int)

        # Own location ID and index
        cls.locating_index = Required(int, default=lambda: next(HasLocation.index_counter))
        cls.locating_order = Optional(int)

    # Index counters
    index_counter = count(1)
    order_counter = count(1)
    children = []

    @lazy_property
    def location(self):
        """Return the object's location or None."""
        if not self.location_entity:
            return

        try:
            entity = getattr(db, self.location_entity)
        except AttributeError:
            return

        try:
            location = entity.get(locating_index=self.location_pkey)
        except OrmError:
            self.location_entity = ""
            self.location_pkey = None
            return

        return location

    @location.setter
    def location(self, new_location):
        """Change the location of this object."""
        if new_location is None:
            self.location_entity = ""
            self.location_pkey = None
        else:
            # First, check that there won't be a location loop
            # (location1 contains location2 contains location3...)
            location = new_location
            while location is not None:
                if location is self:
                    raise RecursionError(
                            f"cannot move {self!r} into {new_location!r}, "
                            f"because {self!r} contains {new_location}"
                    )
                location = location.location

            self.location_entity = type(new_location).__name__
            self.location_pkey = new_location.locating_index
            self.locating_order = next(HasLocation.order_counter)

    @property
    def contents(self):
        """Return the objet's contents as a list."""
        contents = []
        name = type(self).__name__
        for cls in HasLocation.children:
            contents += list(select(child for child in cls if
                    child.location_entity == name and
                    child.location_pkey == self.locating_index))

        contents.sort(key=lambda child: child.locating_order)
        return contents
