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

"""Non-playing character entity."""

from typing import Sequence

from pony.orm import Optional

from data.character import Character

class NPC(Character):

    """Non-playing character."""

    prototype = Optional("CharacterPrototype")
    origin = Optional("Room", reverse="has_spawned")

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
        if len(group) == 1:
            return self.names.singular
        else:
            return f"{len(group)} {self.names.plural}"
