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

"""Blueprint entity."""

from datetime import datetime
from importlib import import_module
from pathlib import Path
from typing import Callable, Union

from logbook import FileHandler, Logger
from pony.orm import Required
from yaml import safe_load_all

from data.base import db, PicklableEntity
from data.blueprints.blueprint import Blueprint as BP
from data.blueprints.parser.base import AbstractParser
from data.mixins import HasMixins
import settings

# Logger
logger = Logger()
file_handler = FileHandler("logs/blueprints.log",
        encoding="utf-8", level="DEBUG", delay=True)
file_handler.format_string = (
        "{record.time:%Y-%m-%d %H:%M:%S.%f%z} [{record.level_name}] "
        "{record.message}"
)
logger.handlers.append(file_handler)

PARENT = Path("blueprints")

class Blueprint(PicklableEntity, db.Entity, metaclass=HasMixins):

    """
    Keep track of the applied blueprints.

    A blueprint is a file in YML format, stored in the blueprints/
    directory.  Each file is applied when the game starts, but the
    file path and their modification date is stored in the database,
    so that they're not applied unless they're modified again.

    """

    modified = Required(datetime)
    path = Required(str)

    @classmethod
    def apply_all(cls):
        """Apply all applicable blueprints."""
        parser_module = settings.BLUEPRINT_PARSER
        module = import_module(f"data.blueprints.parser.{parser_module}")
        parsers = [obj for obj in module.__dict__.values() if
                isinstance(obj, type) and issubclass(obj, AbstractParser)
                and obj is not AbstractParser]
        if len(parsers) != 1:
            raise ValueError(f"ambiguous parser in {module}: {parsers}")

        parser = parsers[0]
        # Get settings
        options = {key[10:].lower(): value for
                key, value in settings.__dict__.items() if key.startswith(
                "BLUEPRINT_")}
        options.pop("parser")
        parser = parser(**options)
        parser.retrieve_blueprints()
        parser.apply()

