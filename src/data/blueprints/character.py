# Copyright (c) 2020, LE GOFF Vincent
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

"""Blueprint document for characters."""

from data.base import db
from data.blueprints.document import Document
from data.blueprints.exceptions import DelayMe

class CharacterDocument(Document):

    """Character document to add exits in blueprints."""

    doc_type = "character"
    doc_dump = False
    fields = {
        "name": {
            "type": "str",
            "max_len": 128,
            "presence": "required",
        },
        "account": {
            "type": "str",
            "max_len": 64,
            "presence": "required",
        },
        "permissions": {
            "type": "str",
            "max_len": 64,
            "presence": "optional",
        },
    }

    def apply(self):
        """Apply the document, create or update a character."""
        account = db.Account.get(username=self.cleaned.account)
        if account is None:
            raise DelayMe

        # If the character already exists
        character = db.Character.get(name=self.cleaned.name)
        if character is None:
            character = db.Character(name=self.cleaned.name)

        # Add character to account, if necessary
        if character not in account.characters:
            account.characters.add(character)

        # Add permissions to the character, if necessary
        for permission in self.cleaned.permissions.split():
            if permission:
                character.permissions.add(permission)

        self.objects = (character, )
