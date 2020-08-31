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

import inspect
from datetime import datetime
import pickle
from string import Formatter

from pony.orm import Optional, Required, Set

from command.layer import StaticCommandLayer
from command.stack import CommandStack
from data.base import db, PicklableEntity
from data.mixins import (
        HasAttributes, HasCache, HasLocation, HasMixins, HasPermissions,
        HasStorage, HasTags
)
from data.properties import lazy_property
import settings

class Character(HasAttributes, HasCache, HasLocation, HasPermissions,
        HasStorage, HasTags, PicklableEntity, db.Entity, metaclass=HasMixins):

    """Character entity."""

    name = Required(str, max_len=128)
    session = Optional("Session")
    account = Optional("Account")
    created_on = Required(datetime, default=datetime.utcnow)
    db_command_stack = Optional(bytes)

    async def move_to(self, exit):
        """Move to the specified exit."""
        self.location = exit.destination_for(self.location)
        await self.msg(self.location.look(self))

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

    async def msg(self, text, variables=None):
        """
        Send text to the connected session, if any.

        """
        formatter = VariableFormatter(self, variables)
        text = formatter.format(text)
        if self.session:
            await self.session.msg(text)


UNKNOWN = object()

class VariableFormatter(Formatter):

    """Formatter specifically designed for variables in messages."""

    def __init__(self, character, variables=None):
        self.character = character
        self.variables = variables
        if variables is None:
            self.variables = {}
            frame = inspect.currentframe().f_back
            while frame and (locals := frame.f_locals):
                variables.update(dict(locals))
                frame = frame.f_back

    def get_field(self, field_name, args, kwargs):
        """
        Retrieve the field name.

        The field name might be found in the local variables of
        the previous frames.

        """
        full_name = field_name
        names = field_name.split(".")
        field_name = names[0]
        if field_name.isdigit() or field_name in kwargs:
            return super().get_field(full_name, args, kwargs)

        value = self.variables.get(field_name, UNKNOWN)
        if value is not UNKNOWN:
            for name in names[1:]:
                value = getattr(value, name)

            return (value, full_name)

        raise ValueError(f"cannot find the variable name: {field_name!r}")

    def format_field(self, value, format_spec):
        """
        Add support for simple pluralization.

        The syntax can be used on integer formatters like this:

            >>> num = 1
            >>> "I see {num} {num:dog/dogs}"
            'I see 1 dog'
            >>> num = 2
            >>> "I see {num} {num:dog/dogs}"
            'I see 2 dogs'

        The syntax is as follows: first the identifier
        between braces which should refer to an integer, then a
        colon (:), then the singular name, a slash (/) and
        the plural name.  The singular name will be selected
        if the number is 1, otherwise, the plural name will
        be selected.

        In the previous example, the number to format, called `num`,
        is in a variable defined before calling the formatter.  The
        formatter will look for the variable value and will choose
        which word to display based on this value.  Here are more examples:

            >>> num_dogs = 1
            >>> "There {num_dogs:is/are} {num_dogs} {num_dogs:dog/dogs} here!"
            'There is 1 dog here!'
            >>> apples = 4
            >>> oranges = 1
            >>> "I have {oranges} {oranges:orange/oranges} and " \
            ...     "{apples} {apples:apple/apples}."
            'I have 1 orange and 4 apples.'

        """
        if len(format_spec) > 1 and "/" in format_spec[1:]:
            singular, plural = format_spec.split('/')
            if value == 1:
                return singular
            else:
                return plural
        else:
            return super().format_field(value, format_spec)
