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

"""Attribute module."""

import pickle

from pony.orm import Required, Set

from data.base import db

class Attribute(db.Entity):

    name = Required(str, max_len=32)
    value = Required(bytes)

    @property
    def owner(self):
        return None


class SessionAttribute(Attribute):

    session_owner = Required("Session")

    @property
    def owner(self):
        return self.session_owner


class AccountAttribute(Attribute):

    account_owner = Required("Account")

    @property
    def owner(self):
        return self.account_owner


class AttributeHandler:

    """Attribute handler."""

    def __init__(self, holder):
        self.__holder = holder

    def all(self):
        """Return all the attributes owned by self."""
        return list(self.__holder.attributes)

    def __getattr__(self, attr_name: str):
        """Get a non-existent attribute."""
        candidates = self.__holder.attributes.filter(lambda a: a.name == attr_name)
        if len(candidates) > 1:
            raise ValueError(f"many attributes of the name {attr_name!r} exist")
        elif len(candidates) == 1:
            attribute = candidates.first()
            return pickle.loads(attribute.value)

        return None

    def __setattr__(self, attr_name, value):
        """Set an attribute."""
        if attr_name.startswith("_"):
            super().__setattr__(attr_name, value)
            return

        candidates = self.__holder.attributes.filter(lambda a: a.name == attr_name)
        value = pickle.dumps(value)
        if len(candidates) > 1:
            candidates.delete(bulk=True)
        elif len(candidates) == 1:
            attribute = candidates.first()
            attribute.value = value
            return

        self.__holder.attributes.create(name=attr_name, value=value)
