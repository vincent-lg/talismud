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

"""Delay entity."""

import asyncio
from datetime import datetime, timedelta
from importlib import import_module
from inspect import iscoroutine
from pathlib import Path
import pickle
from typing import Callable, Union

from logbook import FileHandler, Logger
from pony.orm import Required

from data.base import db, PicklableEntity
from data.mixins import HasMixins

# Logger
logger = Logger()
file_handler = FileHandler("logs/delays.log",
        encoding="utf-8", level="DEBUG", delay=True)
file_handler.format_string = (
        "{record.time:%Y-%m-%d %H:%M:%S.%f%z} [{record.level_name}] "
        "{record.message}"
)
logger.handlers.append(file_handler)

class Delay(PicklableEntity, db.Entity, metaclass=HasMixins):

    """
    Delayed action, to be executed after some time.

    A Delay (delayed action) is similar to a callback that will
    be called after some time.  It is stored in the database, so
    that these actions can persist and run even after a game restart.

    A delay is composed of:
        A moment when it should be executed (datetime).
        A Python path leading to the module and callback (str).
        The optional positional arguments to send to the callback.
        The optional keyword arguments to send to the callbacki.

    The positional and keyword arguments are pickled.

    To create a new delayed action, use the `call_in` method like this:

        Delay.call_in(seconds, callback, *args, **kwargs)

    Where `seconds` is the number of seconds in which the delay must
    be executed and `callback` is a callable (the location and
    callable name are extracted from this callable).

    Keep in mind that a valid callable is either:
        * A top-level function defined in a module.
        * A class method or static method.
        * An instance method.  In this case, however, the Python path
          stores the path to the class method name and the instance is
          pickled as a first argument.

    The specified callback can also be a coroutine, which makes things
    easier to call asynchronous code.

        async def tell(character):
            await character.msg("The end.")

        Delay.call_in(5, tell(character))
        # ... or, but less user-friendly
        Delay.call_in(3, tell, character)

    """

    expire_at = Required(datetime)
    py_path = Required(str, max_len=64)
    args = Required(bytes, default=pickle.dumps([]))
    kwargs = Required(bytes, default=pickle.dumps({}))

    @classmethod
    def call_in(cls, seconds: Union[int, float], callable: Callable,
            *args, **kwargs):
        """
        Create a delayed action and call it in X seconds.

        Args:
            seconds (int or float): the seconds in which the callable
                    must be called.
            callable (Callable): the callable to call.

        Optional positional and keyword arguments are supported
        and they will be sent to the callable when the time comes
        to execute it.

        """
        instance = getattr(callable, "__self__", None)
        if iscoroutine(callable):
            # Look for the module
            filename = Path(callable.cr_code.co_filename)
            absolute = Path().absolute()
            relative = filename.relative_to(absolute)
            name = ".".join(relative.parts)
            name = name[:-3]
            name += f".{callable.__qualname__}"
            args = ()
            kwargs = callable.cr_frame.f_locals
        elif instance: # Instance or classmethod
            if isinstance(instance, type): # Class method
                ccls = instance
            else: # Instance method
                ccls = instance.__class__
                args = (instance, ) + args

            name = f"{ccls.__module__}.{ccls.__name__}.{callable.__name__}"
        else:
            name = f"{callable.__module__}.{callable.__name__}"

        expire_at = datetime.utcnow() + timedelta(seconds=seconds)
        delay = cls(expire_at=expire_at, py_path=name, args=pickle.dumps(args),
                kwargs=pickle.dumps(kwargs))
        loop = asyncio.get_event_loop()
        loop.call_later(seconds, delay._execute)
        logger.debug(
            f"Preparing to call {callable} in {seconds} seconds "
            f"({args=}, {kwargs=})")

    def _execute(self):
        """Prepare to execute."""
        loop = asyncio.get_event_loop()
        loop.create_task(self._async_execute())

    async def _async_execute(self):
        """Execute the delayed action."""
        try:
            args = pickle.loads(self.args)
            kwargs = pickle.loads(self.kwargs)
            callable = self._retrieve_callable()
            logger.debug(f"Calling {callable} now ({args=}, {kwargs=})")
            await callable(*args, **kwargs)
        except Exception:
            logger.exception("An error occurred while executing a callbac,:")
        finally:
            logger.debug("Prepare to delete the delay")
            self.delete()

    def _retrieve_callable(self):
        """Retrieve the callable from the Python path."""
        module_path, callable_name = self.py_path.rsplit(".", 1)
        try:
            node = module = import_module(module_path)
        except ModuleNotFoundError:
            # Assume the module path also contains a class name
            module_path, class_name = module_path.rsplit(".", 1)
            module = import_module(module_path)
            node = getattr(module, class_name)

        return getattr(node, callable_name)

    @classmethod
    def schedule(self):
        """Schedule all recorded delays in the database."""
        loop = asyncio.get_event_loop()
        now = datetime.utcnow()
        for delay in Delay.select():
            delta = delay.expire_at - now
            seconds = delta.total_seconds()
            if seconds < 0:
                seconds = 0

            logger.debug(f"Calling callback in {seconds} seconds.")
            loop.call_later(seconds, delay._execute)
