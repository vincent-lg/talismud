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

"""Locator handler, to handle flexible object location."""

from collections import defaultdict

from pony.orm import (
        Optional, Required, Set, commit, composite_index, exists, select,
)

from data.base import db
from data.cache import CACHED

LOCATIONS = {}
CONTENTS = {}
CACHED["contents"] = CONTENTS
CACHED["locations"] = LOCATIONS

class LocatorHandler:

    """Locator handler, to handle flexible location."""

    max_index = None

    def __init__(self, owner):
        self._owner = owner
        self._object_class = owner.__class__.__name__
        if owner.id is None:
            commit()
        self._object_id = owner.id
        self.index = None

    def get(self):
        """Retrieve the location of the owner."""
        if (cached := LOCATIONS.get(self._owner)):
            return cached

        locator = Location.get(object_class=self._object_class,
                object_id=self._object_id)
        if locator:
            Entity = getattr(db, locator.location_class)
            location = Entity[locator.location_id]
            if location:
                LOCATIONS[self._owner] = location
            return location

        return None

    def set(self, location):
        """
        Change the location of the owner.

        Args:
            location (Any): the new location.

        Raises:
            RecursionError: the new location breaks the
                    location/content contract (E.G. A contains B
                    contains A...).

        """
        max_index = type(self).max_index
        if max_index is None:
            # Retrieve the maximum index
            max_index = select(location.index for location in Location).max()
            max_index = max_index or 0
            type(self).max_index = max_index

        # Check the location recursively.
        # It might be possible to optimize it.  As it stands, we need
        # to iterate over locations, not ideal, though acceptable with
        # a limited depth set of data.
        if location is not None:
            object_class, object_id = type(location).__name__, location.id
            while object_class:
                if (object_class == self._object_class and
                        object_id == self._object_id):
                    raise RecursionError

                t_location = Location.get(object_class=object_class,
                        object_id=object_id)
                if t_location:
                    object_class = t_location.location_class
                    object_id = t_location.location_id
                else:
                    break

        old_location = self.get()
        locator = Location.get(object_class=self._object_class,
                object_id=self._object_id)
        if locator:
            if location is None:
                locator.delete()
                return

            locator.location_class = type(location).__name__
            locator.location_id = location.id
            locator.index = type(self).max_index + 1
        elif location is not None:
            Location(object_class=self._object_class,
                    object_id=self._object_id,
                    location_class=type(location).__name__,
                    location_id=location.id, index=type(self).max_index + 1)

        type(self).max_index += 1

        # Affect the cached location and contents
        LOCATIONS[self._owner] = location
        if old_location:
            old_contents = CONTENTS.get(old_location, [])
            if self._owner in old_contents:
                old_contents.remove(self._owner)
        if location:
            new_contents = CONTENTS.get(location, [])
            if not new_contents:
                CONTENTS[location] = new_contents
            new_contents.append(self._owner)

    def contents(self):
        """Return the contents of the owner, sorted by index."""
        location = self.get()
        cached = CONTENTS.get(location, None)
        if cached is not None:
            return cached

        contents = select(location for location in Location
                if location.location_class == self._object_class and
                location.location_id == self._object_id)
        object_classes = defaultdict(list)
        indice = 0
        indices = {}
        for location in contents:
            Entity = getattr(db, location.object_class)
            object_classes[Entity].append(location.object_id)
            indices[(Entity, location.object_id)] = indice
            indice += 1

        # Retrieve the object locations
        objects = [None] * indice
        for Entity, ids in object_classes.items():
            for obj in select(obj for obj in Entity if obj.id in ids):
                index = indices[(type(obj), obj.id)]
                objects[index] = obj

        return objects


class Location(db.Entity):

    """An entity to flexibly link an object with its location."""

    object_class = Required(str)
    object_id = Required(int)
    composite_index(object_class, object_id)
    location_class = Required(str)
    location_id = Required(int)
    index = Required(int, unique=True)

    @property
    def str_id(self):
        """Return the string identifier (object_class:object_id)."""
        return f"{self.object_class}:{self.object_id}"
