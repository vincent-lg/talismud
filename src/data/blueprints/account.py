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

"""Blueprint document for accounts.

It is rare to place accounts in blueprints and this can be a security
risk, should the blueprints be shared with others.  If
you have to place accounts in blueprints, remember to keep it light
and only build the bare minimum for testing (an admin account,
a player account).

WARNING: an account blueprint contains the account password.
Keep that in mind before sharing the file.

"""

from typing import Optional

from data.base import db
from data.blueprints.document import Document
from data.blueprints.exceptions import BlueprintAlert, DelayMe, DelayDocument

class AccountDocument(Document):

    """Account document to add accounts in blueprints."""

    doc_type = "account"
    doc_dump = True
    fields = {
        "username": {
            "type": "str",
            "presence": "required",
            "py_attr": "username",
        },
        "password": {
            "type": "str_or_bytes",
            "presence": "required",
            "py_attr": "hashed_password",
        },
        "email": {
            "type": "str",
            "presence": "optional",
            "py_attr": "email",
        },
        "players": {
            "type": "subset",
            "document_type": "player",
            "py_attr": "players",
        },
    }

    def register(self):
        """Register the object for the blueprint."""
        self.object = None
        if (account := db.Account.get(username=self.cleaned.username)):
            self.object = account
            self.blueprint.objects[account] = self
            return (account, )

        return ()

    def apply(self):
        """Apply the document, create or update an account."""
        username = self.cleaned.username
        password = self.cleaned.password
        email = self.cleaned.email

        # Hash the password if necessary
        if isinstance(password, str):
            password = db.Account.hash_password(password)

        account = self.object
        if account is None:
            account = db.Account(username=username,
                    hashed_password=password, email=email)
            account.blueprints.add(self.blueprint.name)
        else:
            account.hashed_password = password
            account.email = email
        self.blueprint.objects[account] = self

        # Add the players
        for player in list(self.cleaned.players):
            try:
                player.apply()
            except DelayMe:
                self.cleaned.players.remove(player)
                raise DelayDocument(player)
