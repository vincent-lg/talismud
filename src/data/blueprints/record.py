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

"""Blueprint record entity, to keep track of appliesd blueprints."""

from datetime import datetime
from importlib import import_module
import typing as ty

from pony.orm import PrimaryKey, Required

from data.base import db, PicklableEntity
from data.blueprints.parser.base import AbstractParser
import settings

class BlueprintRecord(PicklableEntity, db.Entity):

    """
    Blueprint record entity, complement to the blueprint tag.

    A blueprint is a description of several documents, with each
    document being a building block of the game (like a room).
    In the default paser, blueprints are files in YML format,
    stored in the 'blueprints/' directory.  Each file is applied
    when the game starts, but the file path and its modification
    date is stored in the database, so that they're the file isn't
    applied unless it has been modified again.  This logic can
    be applied to other parsers: the blueprint record defined
    here contains just a unique name (the name of the blueprint
    to apply) and when it was applied.  How to apply (or not
    to apply) is left to the parser.

    """

    name = PrimaryKey(str)
    modified = Required(datetime)

    @classmethod
    def apply_all(cls):
        """Apply all applicable blueprints."""
        # Get all records in a dictionary
        records = cls.select()
        records = {record.name: record for record in records}

        # Create a parser following the settings
        parser_module = settings.BLUEPRINT_PARSER
        module = import_module(f"data.blueprints.parser.{parser_module}")
        parsers = [obj for obj in module.__dict__.values() if
                isinstance(obj, type) and issubclass(obj, AbstractParser)
                and obj is not AbstractParser]
        if len(parsers) != 1:
            raise ValueError(f"ambiguous parser in {module}: {parsers}")

        parser = parsers[0]

        # Get additional settings for this parser
        options = {key[10:].lower(): value for
                key, value in settings.__dict__.items() if key.startswith(
                "BLUEPRINT_")}
        options.pop("parser")

        # Instanciate the parser object
        parser = parser(records, **options)

        # Retrieve and apply blueprints, leaving this task to the parser
        parser.retrieve_blueprints()
        parser.apply()
