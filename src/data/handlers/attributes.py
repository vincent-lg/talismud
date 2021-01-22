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

"""Attribute handler, to handle database attributes."""

import pickle
import typing as ty

from pony.orm import PrimaryKey, Required, commit, exists, select

from data.base import db

NOT_SET = object()

class AttributeHandler:

    """Attribute handler."""

    subset = "attribute"

    def __init__(self, owner):
        self.__owner = owner
        self.__object_class = owner.__class__.__name__
        if owner.id is None:
            commit()
        self.__object_id = owner.id

    def __getattr__(self, name):
        """Return the attribute value or raises AttributeError."""
        return self._get_attribute_of_name(name).value

    def __setattr__(self, name, value):
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            attr = self._get_attribute_of_name(name, default=None)
            if attr:
                attr.pickled = pickle.dumps(value)
            else:
                Attribute(subset=self.subset, object_class=self.__object_class,
                        object_id=self.__object_id, name=name,
                        pickled=pickle.dumps(value))

    def __delattr__(self, name):
        """Remove this attribute."""
        if name.startswith("_"):
            super().__delattr__(name)
        else:
            attr = self._get_attribute_of_name(name, default=None)
            if attr:
                attr.delete()
            else:
                raise ValueError("this attribute doesn't exist")

    def __iter__(self):
        """Iterate over the attributes."""
        return iter(self._get_all_attributes()[:])

    def __contains__(self, name):
        """Return whether this instance contains the named attribute."""
        return exists(attr for attr in self._get_all_attributes()
                if attr.name == name)

    def __len__(self):
        """Return the number of stored attributes for this instance."""
        return len(self._get_all_attributes()[:])

    def get(self, attribute: str, default: ty.Optional[ty.Any] = NOT_SET):
        """
        Return the attribute or default if set.

        Args:
            attribute (str): the name of the attribute.

        Raises:
            ValueError: the attribute wasn't found and no default was
                    supplied.

        Returns:
            value or default: the value of the attribute, or default.

        """
        return self._get_attribute_of_name(attribute, default=default,
                value=True)

    def _get_all_attributes(self):
        """Return the attributes for this object."""
        return select(attribute for attribute in Attribute
                if attribute.subset == self.subset
                and attribute.object_class == self.__object_class and
                attribute.object_id == self.__object_id)

    def _get_attribute_of_name(self, name, default=NOT_SET, value=False):
        """Return the attribute of this name, or raise an exception."""
        result = select(attr for attr in self._get_all_attributes()
                if attr.name == name)[:]
        if result:
            if value:
                return result[0].value

            return result[0]

        if default is not NOT_SET:
            return default

        raise ValueError("uknown attribute")

    @classmethod
    def _query_all(cls):
        """Query all attributes in this subset, reutning the query."""
        return select(attribute for attribute in Attribute
                if attribute.subset == cls.subset)


class Attribute(db.Entity):

    """Database attribute, linked to any object."""

    subset = Required(str)
    object_class = Required(str)
    object_id = Required(int)
    name = Required(str)
    PrimaryKey(subset, object_class, object_id, name)
    pickled = Required(bytes)

    @property
    def value(self):
        """Return the unpickled value."""
        return pickle.loads(self.pickled)

    def __repr__(self):
        return f"<Attribute {self.name!r}>"
