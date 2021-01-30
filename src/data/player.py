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

"""Player entity.

A player is a character with a name, and it can be linked to an account.

"""

from datetime import datetime
import pickle
from pony.orm import Optional, Required

from context.stack import ContextStack
from data.character import Character
from data.decorators import lazy_property

class Player(Character):

    """Playing Character (PC)."""

    name = Required(str)
    account = Required("Account")
    created_on = Required(datetime, default=datetime.utcnow)
    binary_context_stack = Optional(bytes)

    @lazy_property
    def context_stack(self):
        """Return the stored or newly-build context stack."""
        stored = self.binary_context_stack
        if stored:
            return pickle.loads(stored)

        # Create a new context stack
        stack = ContextStack(self)

        # Add the static command layer as first layer
        stack.add_command_layer("static")
        return stack

    def after_insert(self):
        """
        Hook called before the player is inserted.

        We take this opportunity to add the player name as a singular name.

        """
        self.names.singular = self.name
