"""Mixin to add support for descriptions.

To add a description to an entity, add the `HasDescription` mixin.
Entities are created dynamically to allow dynamic description allocation
on various entities.  In other words, if you inherit `Room` from
`HasDescription`, it will create a `RoomDescription` dynamic entity,
and `room.description` will be a link to `RoomDescription` entity.

"""

from textwrap import fill
import typing as ty

from pony.orm import Optional, Required, Set
from pony.orm.core import Index

from data.base import db
from data.properties import lazy_property

class HasDescription:

    """
    Mixin to add a description to an entity.
    """

    @staticmethod
    def extend_entity(cls):
        """Add entity attributes to the entity."""
        # Generate the corresponding description entity
        description_entity = f"{cls.__name__}Description"
        plural = f"{cls.__name__.lower()}s"
        fields = {
            "_table": description_entity,
            plural: Set(cls.__name__),
        }
        entity = type(description_entity, (Description, ), fields)
        cls.description = Optional(description_entity)


class Description(db.Entity):

    """Abstract description entity."""

    text = Required(str)

    def format(self, vars: ty.Optional[ty.Dict[str, str]] = None,
            ident_with: str = " " * 3, ident_no_wrap: bool = False,
            width: int = 78) -> str:
        """
        Format the description and return a formatted string.

        Args:
            vars (dict, optional): the variables for dynamic descriptions.
            ident_with (str, optional): the text to add before
                    each paragraph to indent, usually three spaces
                    or nothing.
            ident_no_wrap (bool, optional): add `ident_with` before
                    a paragraph, even if doing so wouldn't require
                    wrapping it to several lines.  If False (the default),
                    a paragraph that only contains one line will not
                    be indented.
            width (int, optional): the maximum width of each line.  If
                    set to None, do not wrap anything.

        """
        vars = vars or {}
        paragraphs = self.text.splitlines()

        for num_line, paragraph in enumerate(paragraphs):
            words = paragraph.split(" ")
            for num_word, word in enumerate(words):
                if word.startswith("$"):
                    # Get the variable name, removing ponctuation
                    index = max((i for i in range(1, len(word)) if
                            word[i:i + 1].isalpha()), default=0)
                    if index > 0:
                        variable = word[1:index + 1]
                        value = vars.get(variable, "")
                        words[num_word] = value + word[index + 1:]

            paragraph = " ".join(words)
            limit = width
            if not ident_no_wrap:
                limit -= len(ident_with)

            if len(paragraph) > limit:
                paragraph = ident_with + paragraph
                paragraph = fill(paragraph, width)
            paragraphs[num_line] = paragraph

        return "\n".join(paragraphs)
