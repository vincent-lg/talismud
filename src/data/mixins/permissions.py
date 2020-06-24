"""Mixin to add permissions, using tags.

This mixin needs the `HasTags` mixin to be present on the entity as
well.  Permissions are just a category of tags.

See the `HasTags` mixin (in 'tags.py').

"""

import typing as ty

from data.properties import lazy_property

class HasPermissions:

    """Mixin to add permissions, as tags."""

    @staticmethod
    def extend_entity(cls):
        """Add entity attributes to the entity."""
        cls.permissions = lazy_property(lambda e: PermissionsHandler(e))

class PermissionsHandler:

    """Permissions handler."""

    def __init__(self, holder):
        self.__holder = holder

    def all(self) -> list:
        """
        Return all the permissions on this object.

        Permissions are tags of category "permission".

        Returns:
            tags (list): list of permissions on this object.

        """
        return self.__holder.tags.with_category("permission")

    def has(self, permission_name: str) -> bool:
        """Check if object has this permission set."""
        return self.__holder.tags.has(permission_name, category="permission")

    def add(self, permission_name: str):
        """Set a permission on this object."""
        self.__holder.tags.add(permission_name, category="permission")

    def remove(self, permission_name: str):
        """Remove the given permission from the object."""
        self.__holder.tags.remove(permission_name, category="permission")
