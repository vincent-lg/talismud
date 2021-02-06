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

"""Base classes for data."""

from typing import Sequence

from pony.orm import Database, OrmError, commit

db = Database()

class PicklableEntity:

    """Render the entity picklable."""

    def __reduce__(self):
        # Check that the parent __reduce__ works but don't use it
        if self.get_pk() is None:
            commit()

        reduced = {}
        reduced["class"] = type(self)
        reduced["pk"] = self.get_pk()
        return (retrieve, (reduced, ))

def retrieve(reduced):
    """Retrieve a reduced entity."""
    Entity = reduced.get("class", None)
    pk = reduced.get("pk", None)
    if Entity is None or pk is None:
        return

    try:
        entity = Entity[pk]
    except OrmError:
        return

    return entity


class CanBeNamed:

    """
    Mixin to have instances support naming.

    Naming is handled through two different methods, one of them should be overridden as a bare minimum.


    Hashed names:
        When handling pluralization (the way to obtain a single name for several objects), it is necessary to group these names.  TalisMUD does it bybrowsing the list of objects we want to group (for instance, the list of characters in a room, to display them in the "look" command) and, for each, ask its hashed name.  The hashed name is somewhat similar to the object's singular name (and that's what the method actually returns by default), but it dcan be useful to change how TalisMUD decides such an object can be grouoped with others.
        Method to override: `get_hashable_name`.

    Pluralization:
        When several objects have been grouped, one of them is asked to return a plural name for this group.  Usually, the method should return the number of objects and a plural name (say "4 red apples").  The pluralizationn method, `get_name_for`, is sent the list of objects in the same group, which allows to give a more specific name (though notice that it's too late to "separate" names, they have been grouped at that point and a plural name should be returned).
        Method to override (mandatory): `get_name_for`.

    """

    def get_hashable_name(self, group_for: 'db.Character'):
        """
        Return a hashable name to indicate future grouping.

        By default, this method returns the singular name
        for this object (that is, the `get_name_for`  method with
        only one object, `self`).  However, this can be altered,
        to change the way object names are grouped.

        Args:
            group_for (Character): the character to whom the list of objects
                    will be displayed.

        Returns:
            name (str): the hashable name.

        """
        return self.get_name_for(group_for, (self, ))

    def get_name_for(self, group_for: 'db.Character',
            group: Sequence['CanBeNamed']):
        """
        Return the singular or plural name for this object.

        This method is called to pluralize an object name, or to get
        the singular name if the object couldn't be grouped.

        Args:
            group_for (Character): the character to whom the list
                    of objects will be displayed.
            group (list of objects): the objects in the same group.
                    This list contains `self` and thus,
                    is at least one object in length.

        Returns:
            name (str): the singular or plural name to display, depending.

        """
        raise NotImplementedError
