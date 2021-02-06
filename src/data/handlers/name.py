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

"""Name handler, to handle search in names."""

from pony.orm import select

from data.base import db
from data.decorators import lazy_property
from data.handlers.attributes import AttributeHandler
from data.handlers.tags import TagHandler

## Constants
# Characters to remove.  Removed characters are converted to spaces,
# extra spaces are removed too.  This setting can be set to a
# tuple instead, if you wish to remove patterns with more than one character.
TO_REMOVE = ",;./-'"

# Characters to replace
# This is a dictionary of characters and what they should be
# replaced with.  This might allow to remove accented characters,
# for instance, and replace them with latin equivalents, in some languages.
TO_REPLACE = {
        "\t": " ",
}

# Cached names, to speed up querying
CACHED_NAMES = {}

class NameHandler(TagHandler):

    """Name handler, using a tag handler behind the scenes."""

    subset = "name"

    def __init__(self, owner):
        super().__init__(owner)
        self.common = CommonNames(owner)

    @lazy_property
    def singular(self):
        """Return the singular name."""
        return self._get_common_name("singular")

    @singular.setter
    def singular(self, name: str):
        """Change the singular name."""
        self._set_common_name("singular", name)

    @lazy_property
    def plural(self):
        """Return the plural name."""
        return self._get_common_name("plural")

    @plural.setter
    def plural(self, name: str):
        """Change the plural name."""
        self._set_common_name("plural", name)

    def register(self, name: str):
        """
        Register a name

        Args:
            name (str): the name to register.

        Behind the scenes, the name is split in words (or
        language-appropriate portions) and each portion is stored in
        a tag with a specific subset.  Searching through
        the database (using the `search` class method) will
        search through these names.

        """
        name = self.normalize(name)

        # Add the required tags
        for portion in self.split(name):
            super().add(portion)

    @classmethod
    def search(cls, string: str, limit_to=None):
        """
        Search the given string, returning a list of mathcing objects.

        Args:
            string (str): the string to match.
            limit_to (list of objects, opt): list of objects that
                    should include the limit.

        This can be a piece of the name.  However, by default,
        the specified string should be at the beginning
        of the name (or at the beginning of a word in the name).
        The way names are subscribed is following word division
        with some adjustements for punctuations and other
        symbols.  Hence, if "a white rabbit" is registered,
        searching for "white" or "rab" will work, as well
        as searching for "white rabb", but searching for "hit"
        will not work, because "hit" in "white" is not at the
        beginning of a word.

        """
        string = cls.normalize(string)

        query = cls._get_search_query()
        if limit_to is not None:
            ids = tuple(f"{type(obj).__name__}:{obj.id}" for obj in limit_to)
            query = db.TagLink.select(lambda link: link.str_id in ids)
            query = query.filter(lambda link: link.tag.name.startswith(
                    string))
            query = select(link.tag for link in query)
        else:
            query = query.filter(lambda tag: tag.name.startswith(string))
        objects = cls._get_opbjects_from_query(query)
        if limit_to is not None:
            objects = [obj for obj in objects if obj in limit_to]

        return objects

    @classmethod
    def split(cls, string: str):
        """
        Split the words following the language logic, returning a tuple.

        Args:
            string (str): the string to split.

        Words are split according to separators defined in
        settings.  Considering a simple example where only
        spaces are considered separators, calling this method with
        "a red apple" will produce:
                ('a', 'a red', 'a red apple', 'red', 'red apple', 'apple')`

        """
        words = []
        i = 0
        while i != -1:
            j = i
            while j is not None:
                start = i + 1
                if i == 0:
                    start = None
                j = cls.find_first(string, j + 1)
                if j == -1:
                    j = None
                word = string[start:j]
                words.append(word)
            i = cls.find_first(string, i + 1)

        return tuple(words)

    @classmethod
    def find_first(cls, string: str, i: int):
        """Find the first index of a separator."""
        indices = [string.find(sep, i) for sep in " '-"]
        indices = [index for index in indices if index >= 0]
        return min(indices, default=-1)

    @classmethod
    def normalize(cls, name: str) -> str:
        """
        Normalize the given name, returning a simplified version.

        Punctuation signs may be removed from the name.  Characers
        can be replaced by others (like accented characters
        by their latin equivalent in some languages).
        Extra spaces also are removed.

        Args:
            name (str): the original name.

        Returns:
            normalized (str): the normalized name.

        Note:
            This normalization should occur before registering names
            (`register`) and searching (`search`).

        """
        name = name.lower()

        # Remove useless signs (like punctuation)
        for sign in TO_REMOVE:
            name = name.replace(sign, " ")

        # Replace some characters in the name
        for char, replace_with in TO_REPLACE.items():
            name = name.replace(char, replace_with)

        # Remove extra spaces
        while "  " in name:
            name = name.replace("  ", " ")

        # Remove useless spaces at either end of the name
        name = name.strip()

        return name

    def _get_common_name(self, cat: str):
        """Return the cached common name."""
        object_class = self._TagHandler__object_class
        object_id = self._TagHandler__object_id
        key = f"{object_class}:{object_id}:{cat}"
        if (value := CACHED_NAMES.get(key)) is not None:
            return value

        # If the owner has a prototype, query it.
        prototype = getattr(self._TagHandler__owner, "prototype", None)
        if prototype:
            key = f"{prototype.__class__.__name__}:{prototype.id}:{cat}"
            if (value := CACHED_NAMES.get(key)) is not None:
                return value

        return ""

    def _set_common_name(self, cat: str, name: str):
        """Change the cached name."""
        object_class = self._TagHandler__object_class
        object_id = self._TagHandler__object_id
        key = f"{object_class}:{object_id}:{cat}"
        CACHED_NAMES[key] = name
        setattr(self.common, cat, name)


class CommonNames(AttributeHandler):

    """
    Common names, using attributes.

    These names, stored as attributes, are cached when the game starts,
    and updated in the cache on demand.  This process allows to query them
    quickly.

    """

    subset = "names"

    @classmethod
    def cache_names(cls):
        """Cache all names for all objects."""
        names = cls._query_all()
        for name in names:
            to_cache = (
                    f"{name.object_class}:{name.object_id}:"
                    f"{name.name}"
            )
            CACHED_NAMES[to_cache] = name.value
