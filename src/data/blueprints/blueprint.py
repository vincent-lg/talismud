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

"""Blueprint module, containing the Blueprint class.

A Blueprint is created to handle several documents.  Usually,
a blueprint is a file (a YML file by default, though you can abstract
it to use other document types).  The blueprint will receive a list
of documents and apply them as best it can.  It also offers
the ability to postpone evaluation of documents if needed and can
report back to whatever function called it.

"""

from typing import Any, Dict, Sequence

from data.blueprints.document import create, create_from_object
from data.blueprints.exceptions import DelayMe, DelayDocument

class Blueprint:

    """A blueprint, holding several documents."""

    def __init__(self, name: str, documents: Sequence[Dict[str, Any]]):
        self.name = name
        self.documents = documents
        self.delayed = []
        self.applied = 0
        self.modified = False
        self.objects = {}

        # Document types
        self.rooms = {} # {barcode: document}
        self.coords = {} # {(x, y, z): document}

        for i, document in enumerate(self.documents):
            document = self.create_document(document)
            self.documents[i] = document

    @property
    def dictionaries(self):
        dictionaries = []
        for document in self.documents:
            if not document.doc_dump:
                continue

            dictionary = {"type": document.doc_type}
            dictionary.update(document.dictionary)
            dictionaries.append(dictionary)

        return dictionaries

    def __enter__(self):
        self.modified = False
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def create_document(self, document: Dict[str, Any]):
        """
        Create and add the document to this blueprint.

        Args:
            document (dict): the document to add as a dictionary.

        Returns:
            document (Document): the created document.

        """
        document = create(self, document)

        # Action based on type
        method = getattr(self, f"handle_{document.doc_type}", None)
        if method:
            method(document)

        return document

    def create_document_from_object(self, obj: Any):
        """
        Create and add the document to this blueprint, built from an object.

        Args:
            obj (Any): the object from which to create the document.

        Returns:
            document (Document): the created document.

        """
        document = create_from_object(self, obj)

        # Action based on type
        method = getattr(self, f"handle_{document.doc_type}", None)
        if method:
            method(document)

        return document

    def update_document_from_object(self, obj: Any):
        """
        Update the document linked to an object.

        Args:
            obj (Object): the object to update.

        """
        document = self.objects.get(obj)
        if document is None:
            self.modified = True
            document = self.create_document_from_object(obj)
            self.documents.append(document)
            self.objects[obj] = document
        else:
            old = document.dictionary
            document.fill_from_object(obj)
            new = document.dictionary
            if old != new:
                self.modified = True

    def handle_room(self, document):
        """Handle the room document."""
        with document.cleaned as room:
            self.rooms[room.barcode] = document
            if all(data is not None for data in (
                    room.x, room.y, room.z)):
                x, y, z = room.x, room.y, room.z
                self.coords[(x, y, z)] = document

    def register(self):
        """Register all stored documents."""
        objects = set()
        for document in self.documents:
            for obj in document.register():
                objects.add(obj)

        return tuple(objects)

    def apply(self):
        """
        Apply as many documents as possible.

        If applying a document raises a DelayMe exception,
        this document is ignored and will be applied again later in
        the same method.  If the document still doesn't apply,
        it is added to the `delayed` list.

        """
        delayed = []
        for document in self.documents:
            applied = False
            while not applied:
                try:
                    document.apply()
                except DelayMe:
                    # The document itself should be delayed
                    delayed.append(document)
                    break
                except DelayDocument as exc:
                    delayed.append(exc.document)
                else:
                    applied = True
                    for obj in document.objects:
                        obj.blueprints.add(self.name)

            self.applied += 1


        # Second wave, try to apply the delayed documents
        for document in delayed:
            try:
                document.apply()
            except DelayMe:
                self.delayed.append(document)
            except DelayDocument as exc:
                self.delayed.append(exc.document)
            else:
                self.applied += 1
                for obj in document.objects:
                    obj.blueprints.add(self.name)
