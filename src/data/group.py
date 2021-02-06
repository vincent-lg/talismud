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

"""Module to group objects by their name."""

from collections import defaultdict
from typing import Sequence

from data.base import db, CanBeNamed

def group_names(objects: Sequence[CanBeNamed], group_for: 'db.Character'):
    """
    Return the object names, grouped by quantity.

    Args:
        objects (sequence): the list of objects.
        group_for (Character): the character looking on these objects.

    Note:
        All objects should implement `get_name_for` and
        `get_hashable_name`, thus, it is recommanded to inhave these
        objects inherit from `CanBeNamed`.

    """
    to_hash = defaultdict(list)
    for obj in objects:
        hashed = obj.get_hashable_name(group_for)
        to_hash[hashed].append(obj)

    # Now the names and objects should be sorted.
    names = []
    for grouped in to_hash.values():
        # We know there is at least one object in the list, we ask it to
        # handle the pluralization process.
        name = objects[0].get_name_for(group_for, grouped)
        names.append(name)

    return names
