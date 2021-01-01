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

"""Tag handler, to handle database tags."""

from collections import defaultdict
import typing as ty

from pony.orm import (
        Optional, Required, Set, commit, composite_index, exists, select,
)

from data.base import db

NOT_SET = object()

class TagHandler:

    """Tag handler."""

    subset = "tag"
    category = None

    def __init__(self, owner):
        self.__owner = owner
        self.__object_class = owner.__class__.__name__
        if owner.id is None:
            commit()
        self.__object_id = owner.id

    def __iter__(self):
        """Iterate over the tags."""
        return iter(self._get_all_tags()[:])

    def __contains__(self, name):
        """Return whether this instance contains the named tag."""
        return exists(link for link in self._get_all_tags()
                if link.tag.name == name)

    def __len__(self):
        """Return the number of stored tags for this instance."""
        return len(self._get_all_tags()[:])

    def has(self, name, category=None):
        """
        Return whether this tag is present in this object.

        Args:
            name (str): the name of the tag.
            category (str, optional): the category.

        Returns:
            tagged (bool): whether this object has been tagged.

        The tag category will always be replaced by the limited category
        of the tag handler, if any has been set.

        """
        category = self.category or category
        return self._get_tag_of_name(name, category, default=None) is not None

    def add(self, name, category=None):
        """
        Add the tag to this object.

        If this object has already been tagged, do not raise any error.

        Args:
            name (str): the name of the tag.
            category (optional, str): the category.

        The tag category will always be replaced by the limited category
        of the tag handler, if any has been set.

        """
        subset = self.subset
        category = self.category or category
        if self._get_tag_of_name(name, category, default=None):
            return

        # Create a Tag object, if necessary
        tag = Tag.get(name=name, category=category, subset=subset) or Tag(
                name=name, category=category, subset=subset)

        # Add a new tag to this tag object
        tag.links.create(object_class=self.__object_class,
                object_id=self.__object_id)

    def remove(self, name, category=None):
        """
        Remove the tag from this object.

        If the tag doesn't exist, raise an exception.

        Args:
            name (str): the name of the tag to remove.
            category (str, optional): the category.

        The tag category will always be replaced by the limited category
        of the tag handler, if any has been set.

        """
        link = self._get_tag_of_name(name, category, default=None)
        if link is None:
            raise ValueError("this object is not tagged with this tag")

        tag = link.tag
        link.delete()
        if len(tag.links) == 0:
            tag.delete()

    def clear(self, category=None):
        """
        Remove all tags from this object.

        Args:
            category (str, optional): only remove tags of this category.

        """
        tags = set()
        for link in self._get_all_tags(category)[:]:
            tags.add(link.tag)
            link.delete()

        result = select(tag for tag in Tag if tag in tags
                and len(tag.links) == 0)
        result.delete(bulk=True)

    @classmethod
    def search(cls, name: ty.Optional[str] = None,
            category: ty.Optional[str] = None) -> tuple:
        """
        Search a given tag, return a list of objects maching this tag.

        Args:
            name (str, optional): the tag name.
            category (str, optional): the name of the category.

        Returns:
            objects (list): a list of objects matching this tag.

        Note:
            `name` or `category` should be specified.

        """
        if name is None and category is None:
            raise ValueError("one of 'name' or 'category' argument "
                    "should be specified")

        query = cls._get_search_query(category=category)
        if name:
            query = query.filter(lambda tag: tag.name == name)

        objects = cls._get_opbjects_from_query(query)
        return objects

    def _get_all_tags(self, category=None):
        """Return the tags for this object."""
        subset = self.subset
        category = self.category or category
        result = select(link for link in TagLink
                if link.object_class == self.__object_class and
                link.object_id == self.__object_id and
                link.tag.subset == subset)
        if category:
            result = select(link for link in result
                    if link.tag.category == category)

        return result

    def _get_tag_of_name(self, name, category=None, default=NOT_SET):
        """Return the tag of this name, or raise an exception."""
        subset = self.subset
        category = self.category or category
        result = select(link for link in self._get_all_tags(category)
                if link.tag.name == name)[:]
        if result:
            return result[0]

        if default is not NOT_SET:
            return default

        raise ValueError("uknown tag")

    @classmethod
    def _get_search_query(cls, category=None):
        query = select(tag for tag in Tag if tag.subset == cls.subset)
        if category:
            query = query.filter(category=category)

        return query

    @classmethod
    def _get_opbjects_from_query(cls, query):
        object_classes = defaultdict(set)
        for tag in query:
            for link in tag.links:
                Entity = getattr(db, link.object_class)
                object_classes[Entity].add(link.object_id)

        # Retrieve the tagged objects
        objects = []
        for Entity, ids in object_classes.items():
            for obj in select(obj for obj in Entity if obj.id in ids):
                objects.append(obj)

        # Sort objects by their location index, if they have any
        missing = []
        indices = {}
        for obj in objects:
            if (locator := getattr(obj, "locator", None)):
                str_id = f"{type(obj).__name__}:{obj.id}"
                if (index := locator.index) is not None:
                    indices[str_id] = index
                else:
                    missing.append(str_id)

        # Query missing locations
        if missing:
            locations = db.Location.select(
                    lambda l: l.str_id in missing)
            for location in locations:
                indices[location.str_id] = location.index

        def sort_key(obj):
            str_id = f"{type(obj).__name__}:{obj.id}"
            return indices.get(str_id, 0)

        objects.sort(key=sort_key)

        return objects



class Tag(db.Entity):

    name = Required(str)
    category = Optional(str)
    subset = Required(str)
    composite_index(name, category, subset)
    links = Set("TagLink")


class TagLink(db.Entity):

    """Database tag, linked to any object."""

    tag = Required("Tag")
    object_class = Required(str)
    object_id = Required(int)
    composite_index(object_class, object_id, tag)

    @property
    def str_id(self):
        """Return the string identifier (object_class:object_id)."""
        return f"{self.object_class}:{self.object_id}"

    def __repr__(self):
        tag = self.tag
        category = tag.category
        string = f"<Tag {tag.name!r}"
        if category:
            string += f" (category={category!r})"

        string += ">"
        return string
