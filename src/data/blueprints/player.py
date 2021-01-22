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

"""Blueprint document for player-characters."""

from data.base import db
from data.blueprints.document import Document
from data.blueprints.exceptions import DelayMe

class PlayerDocument(Document):

    """Player document to add players in blueprints."""

    doc_type = "player"
    doc_dump = False
    fields = {
        "name": {
            "type": "str",
            "presence": "required",
            "py_attr": "name",
        },
        "account": {
            "type": "str",
            "presence": "required",
            "py_attr": "account.username",
        },
        "permissions": {
            "type": "str",
            "presence": "optional",
            "py_attr": "permissions.get",
        },
    }

    def apply(self):
        """Apply the document, create or update a player."""
        account = db.Account.get(username=self.cleaned.account)
        if account is None:
            raise DelayMe

        # If the player already exists
        player = db.Player.get(name=self.cleaned.name)
        if player is None:
            player = db.Player(name=self.cleaned.name, account=account)

        # Add player to account, if necessary
        if player not in account.players:
            account.players.add(player)

        # Add permissions to the player, if necessary
        for permission in self.cleaned.permissions.split():
            if permission:
                player.permissions.add(permission)

        self.objects = (player, )
