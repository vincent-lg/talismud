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

"""Character entity, a playing character or non-playing character alike."""

from datetime import datetime
import pickle

from pony.orm import Optional, Required, Set

from command.layer import StaticCommandLayer
from command.stack import CommandStack
from data.attribute import AttributeHandler
from data.base import db, PicklableEntity
from data.mixins import (
        HasCache, HasLocation, HasMixins, HasPermissions,
        HasStorage, HasTags
)
from data.properties import lazy_property
import settings

class Character(HasCache, HasLocation, HasPermissions, HasStorage, HasTags,
        PicklableEntity, db.Entity, metaclass=HasMixins):

    """Character entity."""

    name = Required(str, max_len=128)
    session = Optional("Session")
    account = Optional("Account")
    created_on = Required(datetime, default=datetime.utcnow)
    db_command_stack = Optional(bytes)

    @lazy_property
    def command_stack(self):
        """Return the stored or newly-bulid command stack."""
        stored = self.db_command_stack
        if stored:
            return pickle.loads(stored)

        # Create a new command stack
        stack = CommandStack(self)
        # Add the static command layer as first layer
        stack.add_layer(StaticCommandLayer)
        return stack

    async def msg(self, text):
        """Send text to the connected session, if any."""
        if self.session:
            await self.session.msg(text)
