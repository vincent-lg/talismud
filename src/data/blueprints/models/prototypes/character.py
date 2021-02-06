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

"""Blueprint document for character prototypes."""

from typing import Optional

from data.base import db
from data.blueprints.document import Document
from data.blueprints.exceptions import BlueprintAlert, DelayMe, DelayDocument

import settings

class CharacterPrototypeDocument(Document):

    """Character prototype document to add NPC prototypes in blueprints."""

    doc_type = "char_proto"
    doc_dump = True
    fields = {
        "barcode": {
            "type": "str",
            "presence": "required",
        },
        "singular": {
            "type": "str",
            "presence": "required",
        },
        "plural": {
            "type": "str",
            "presence": "required",
        },
        "description": {
            "type": "str",
            "presence": "required",
        },
    }

    def fill_from_object(self, proto):
        """Draw the document from an object."""
        self.cleaned.barcode = proto.barcode
        self.cleaned.singular = proto.names.singular
        self.cleaned.plural = proto.names.plural
        self.cleaned.description = proto.description.text

    def register(self):
        """Register the object for the blueprint."""
        self.object = None
        if (prototype := db.CharacterPrototype.get(
                barcode=self.cleaned.barcode)):
            self.object = prototype
            self.blueprint.objects[prototype] = self
            return (prototype, )

        return ()

    def apply(self):
        """Apply the document, create a prototype."""
        prototype = self.object
        if prototype is None:
            prototype = db.CharacterPrototype(barcode=self.cleaned.barcode)
            prototype.blueprints.add(self.blueprint.name)

        self.object = prototype
        self.blueprint.objects[prototype] = self
        prototype.names.singular = self.cleaned.singular
        prototype.names.plural = self.cleaned.plural
        description = self.cleaned.description
        if description:
            prototype.description.set(description)
