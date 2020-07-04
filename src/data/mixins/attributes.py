"""Mixin to add support for attributes.

To add attributes to an entity, add the `HasAttributes` mixin.  Entities
are created dynamically to allow dynamic tag allocation on various
entities.  In other words, if you inherit `Room` from `HasAttributes`,
it will create a `RoomAttribute` dynamic entity, and `room.attributes`
will be a set of `RoomAttribute` entities.

"""

import pickle
import typing as ty

from pony.orm import Optional, Required, Set
from pony.orm.core import Index

from data.base import db
from data.properties import lazy_property

class HasAttributes:

    """
    Mixin to add attributes to an entity.
    """

    @staticmethod
    def extend_entity(cls):
        """Add entity attributes to the entity."""
        # Generate the corresponding attribute entity
        attribute_entity = f"{cls.__name__}Attribute"
        plural = f"{cls.__name__.lower()}s"
        fields = {
            "_table": attribute_entity,
            cls.__name__.lower(): Required(cls.__name__),
        }
        entity = type(attribute_entity, (Attribute, ), fields)
        cls.db_attributes = Set(attribute_entity)
        cls.db = lazy_property(_get_attribute_handler)

def _get_attribute_handler(holder):
    """Get the attribute handler."""
    return AttributeHandler(holder)


class Attribute(db.Entity):

    """Abstract attribute entity."""

    name = Required(str, max_len=32)
    value = Required(bytes)

    def __repr__(self):
        return f"<Attr {self.name}>"


class AttributeHandler:

    """Attribute handler."""

    def __init__(self, holder):
        self.__holder = holder

    def all(self):
        """Return all the attributes owned by self."""
        return list(self.__holder.attributes)

    def __getattr__(self, attr_name: str):
        """Get an existent attribute or None."""
        candidates = self.__holder.attributes.filter(
                lambda a: a.name == attr_name
        )
        if len(candidates) > 1:
            raise ValueError(
                    f"many attributes of the name {attr_name!r} exist"
            )
        elif len(candidates) == 1:
            attribute = candidates.first()
            return pickle.loads(attribute.value)

        return None

    def __setattr__(self, attr_name: str, value: ty.Any):
        """Set an attribute."""
        if attr_name.startswith("_"):
            super().__setattr__(attr_name, value)
            return

        candidates = self.__holder.attributes.filter(
                lambda a: a.name == attr_name
        )
        value = pickle.dumps(value)
        if len(candidates) > 1:
            candidates.delete(bulk=True)
        elif len(candidates) == 1:
            attribute = candidates.first()
            attribute.value = value
            return

        self.__holder.attributes.create(name=attr_name, value=value)
