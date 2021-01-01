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

"""Description handler, to handle database descriptions."""

from collections import defaultdict
from textwrap import fill
import typing as ty

from pony.orm import (
        Optional, Required, Set, commit, composite_index, exists, select,
)

from data.base import db

NOT_SET = object()

class DescriptionHandler:

    """Description handler."""

    def __init__(self, owner):
        self.__owner = owner
        self.__object_class = owner.__class__.__name__
        if owner.id is None:
            commit()
        self.__object_id = owner.id
        self.__description = None

    @property
    def text(self):
        """Return the text of the description."""
        if (description := self.get(default=None)):
            return description.text

        return ""

    def get(self, default=NOT_SET):
        """
        Return the description object, if it exists.

        Otherwise, returns a new description, or default if present.

        Args:
            default (any): what to return if there's no description?

        Returns:
            description (Description or default): the description object,
                    if it exists.

        Note:
            This method returns a description object (if no default is
            set), not the str itself.  You can access the str
            using the `text` attribute, but remember no formatting
            is done at this point:

                plain_description = character.description.get().text
                # For simplicity reason, it is equivalent to:
                plain_description = character.description.text

            Much better to use the format method itself:

                formatted = character.description.format(...)

        """
        # If the description has been cached, just return it
        if (description := self.__description):
            return description

        # Query the database, to see if a description object
        # exists for this owner.
        description = Description.get(object_class=self.__object_class,
                object_id=self.__object_id)
        if description:
            self.__description = description
            return description

        # Create a description, if `default` is not set.
        if default is NOT_SET:
            description = Description(object_class=self.__object_class,
                    object_id=self.__object_id, text="")
            self.__description = description
            return description

        # All is said, return default
        return default

    def set(self, description: str):
        """
        Change the description for the owner.

        Args:
            description (str): the new description.

        """
        # Create a Description object, if necessary
        storage = Description.get(object_class=self.__object_class,
                object_id=self.__object_id)
        if storage is None:
            description = Description(object_class=self.__object_class,
                    object_id=self.__object_id, text=description)
            self.__description = description
        else:
            storage.text = description

    def clear(self):
        """
        Forcibly remove the description, if any was created.

        This method doesn't ask for permission, use it with
        care as there is no way to undo this operation.  The only
        time when this method should be called is when the owner
        is destroyed as well.

        """
        if (description := self.get(default=None)):
            self.__description = None
            description.delete()

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


class Description(db.Entity):

    """Flexible storage for a description, connected to an object."""

    object_class = Required(str)
    object_id = Required(int)
    composite_index(object_class, object_id)
    text = Optional(str)
