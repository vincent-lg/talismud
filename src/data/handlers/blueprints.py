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

"""Handler to add blueprints to objects.

Blueprints are internally considered like tags with a different subset,
though some additional methods are implemented.

"""

import typing as ty

from pony.orm import commit, select

from data.base import db
from data.handlers.tags import TagHandler
import settings

class BlueprintHandler(TagHandler):

    """Blueprint handler, using a tag handler behind the scenes."""

    subset = "blueprint"
    current_parser = None

    def get(self, *others):
        """
        Return the blueprints for the owner and additional objects.

        Args:
            *others (list): other objects.

        """
        objects = [self._TagHandler__owner]
        for other in others:
            if other.id is None:
                commit()
            objects.append(other)

        str_ids = tuple(set([f"{type(obj).__name__}:{obj.id}"
                for obj in objects]))
        query = self._get_search_query()
        query = select(link for link in db.TagLink if link.tag in query and link.str_id in str_ids)

        # Get the blueprints
        blueprints = set()
        for link in query:
            blueprint = type(self).current_parser.blueprints.get(link.tag.name)
            if blueprint is None:
                raise ValueError(f"cannot get the blueprint of name {link.tag.name}")

            blueprints.add(blueprint)

        return tuple(blueprints)

    def get_document(self):
        """
        Return the document for this object, if any is stored.

        Returns:
            document (Document or None): the document for this object.

        """
        blueprints = self.get()
        if blueprints:
            return blueprints[0].objects.get(self._TagHandler__owner)

        return None

    def save(self, *others):
        """
        Save all blueprints of the owner object.

        The owner can be tagged with different blueprints.  Save all of them, including other blueprints passed as arguments.

        Args:
            others (optional): other objects whose blueprint should be saved.

        Note:
            Saving several blueprints at once is more optimized.  For
            instance, let's assume you need to save a room and its
            exit.  There's no telling whether these two objects
            are in the same blueprint, so you could do something like this:

                >>> exit.blueprints.save()
                >>> room.blueprints.save()

            On the other hand, if both are in the same blueprint,
            this will force two file writes and lose much time.
            Better to do:

                >>> exit.blueprints.save(room)

            This will force to save both exit blueprints and
            room blueprints, but will do it more intelligently and
            will avoid the trap described above, saving only
            unique blueprints.

        """
        blueprints = self.get(*others)
        objects = (self._TagHandler__owner, ) + tuple(others)

        for blueprint in blueprints:
            with blueprint:
                for obj in objects:
                    blueprint.update_document_from_object(obj)

            if blueprint.modified:
                type(self).current_parser.store_blueprint(blueprint)

    @classmethod
    def search(cls, name: ty.Optional[str] = None,
            category: ty.Optional[str] = None) -> tuple:
        """
        Search a given blueprint, return a list of objects matching it.

        Args:
            name (str, optional): the blueprint unique name.
            category (str, optional): the name of the category.

        Returns:
            objects (list): a list of objects matching this blueprint.

        Note:
            `name` or `category` should be specified.

        """
        return super().search(name, category)
