"""Mixin to add support for tags.

To add tags to an entity, add the `HasTags` mixin.  Entities are
created dynamically to allow dynamic tag allocation on various
entities.  In other words, if you inherit `Room` from `HasTags`,
it will create a `RoomTag` dynamic entity, and `room.tags` will be
a set of `RoomTag` entity.

"""

import typing as ty

from pony.orm import Optional, Required, Set
from pony.orm.core import Index

from data.base import db
from data.properties import lazy_property

class HasTags:

    """
    Mixin to add tags to an entity.
    """

    @staticmethod
    def extend_entity(cls):
        """Add entity attributes to the entity."""
        # Generate the corresponding tag entity
        tag_entity = f"{cls.__name__}Tag"
        plural = f"{cls.__name__.lower()}s"
        fields = {
            "_table": tag_entity,
            plural: Set(cls.__name__),
            "objects": property(lambda t: getattr(t, plural, [])),
        }
        #fields['_indexes_'] = [Index(fields['first_name'],fields['last_name'],is_pk=False,is_unique=False)]
        entity = type(tag_entity, (Tag, ), fields)
        cls.db_tags = Set(tag_entity)
        cls.tags = lazy_property(_get_tag_handler)

def _get_tag_handler(holder):
    """Get the tag handler."""
    return TagHandler(holder)


class Tag(db.Entity):

    """Abstract tag entity."""

    name = Required(str, max_len=32)
    category = Optional(str, max_len=32)

    def __repr__(self):
        res = f"<Tag {self.name}"
        if self.category:
            res += f" (category={self.category})"
        res += ">"
        return res

    @classmethod
    def search(cls, tag_name: str, category: ty.Optional[str] = None
            ) -> ty.Set[db.Entity]:
        """
        Search all objects having a given tag and optional category.

        Return all objects (characters, rooms) matching the search
        query, in no specific order.

        Args:
            tag_name (str): the name of the tag.
            category (str, optional): the optional tag category.

        Returns:
            objects (set of objects): the objects with this tag and
                    optional category.

        """
        tags = cls.select(lambda t: t.name == tag_name)
        if category is not None:
            tags = tags.filter(category=category)

        objects = set()
        for tag in tags:
            for obj in tag.objects:
                objects.add(obj)

        return objects

class TagHandler:

    """Tag handler."""

    def __init__(self, holder):
        self.__holder = holder

    def all(self) -> list:
        """
        Return all the tags on this object, regardless of category.

        Returns:
            tags (list): list of tags on this object.

        """
        return list(self.__holder.db_tags)

    def with_category(self, category: str) -> list:
        """
        Return all the tags on this object, in the given category.

        Args:
            category (str): the category name.

        Returns:
            tags (list): list of tags on this object, in this category.

        """
        return list(self.__holder.db_tags.filter(
                lambda t: t.category == category))

    def has(self, tag_name: str, category: ty.Optional[str] = None) -> bool:
        """Check if object has this tag."""
        tags = self.__holder.db_tags.filter(lambda t: t.name == tag_name)
        if category is not None:
            tags = tags.filter(category=category)

        return len(tags) >= 1

    def add(self, tag_name: str, category: ty.Optional[str] = None):
        """Set a tag."""
        entity_name = type(self.__holder).__name__
        tag_entity_name = f"{entity_name}Tag"
        tag_entity = getattr(db, tag_entity_name)
        tags = tag_entity.select(lambda t: t.name == tag_name)
        if category is not None:
            tags = tags.filter(category=category)

        if len(tags) >= 1:
            entities = f"{entity_name.lower()}s"
            tag = tags.first()
            getattr(tag, entities).add(self.__holder)
        else:
            category = category if category else ""
            self.__holder.db_tags.create(name=tag_name, category=category)

    def remove(self, tag_name: str, category: ty.Optional[str] = None):
        """Remove the given tag."""
        tags = self.__holder.db_tags.filter(lambda t: t.name == tag_name)
        if category is not None:
            tags = tags.filter(category=category)

        tag = tags.first()
        if tag:
            self.__holder.db_tags.remove(tag)
