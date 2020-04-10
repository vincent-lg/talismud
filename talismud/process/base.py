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

"""The abstract process class."""

from abc import ABCMeta, abstractmethod
import asyncio
from importlib import import_module
import os
from subprocess import Popen
import sys
from typing import Tuple

from logbook import FileHandler, StreamHandler

from process.log import ProcessLogger

class Process(metaclass=ABCMeta):

    """
    Abstract class for a process.

    This class both contains code that will be called in the main process,
    and code to be called when the child process has been created.

    """

    name: str
    services: Tuple[str] = ()

    def __init__(self):
        self.started = False
        self.services = {}
        self.pid = None
        self.logger = ProcessLogger(self)

        # Configure the process logger
        self.file_handler = FileHandler(f"logs/{self.name}.log",
                encoding="utf-8", level="DEBUG", delay=True)
        self.file_handler.format_string = (
                "{record.time:%Y-%m-%d %H:%M:%S.%f%z} [{record.level_name}] "
                "{record.message}"
        )
        self.stream_handler = StreamHandler(sys.stdout, encoding="utf-8",
                level="INFO", bubble=True)
        self.stream_handler.format_string = (
                "[{record.level_name}] {record.channel}: {record.message}"
        )
        self.file_handler.push_application()
        self.stream_handler.push_application()

    def __repr__(self):
        desc = f"<Process {self.name}, "
        if self.started:
            desc += f"running on PID={self.pid}"
        else:
            desc += "not running"
        desc += ">"
        return desc

    async def start(self):
        """Called when the process start."""
        self.should_stop = asyncio.Event()
        self.logger.debug("Starting process...")
        for name in type(self).services:
            module_name = f"service.{name}"
            module = import_module(module_name)
            cls = getattr(module, "Service")
            service = cls(process=self)
            self.services[name] = service
            await service.start()

        self.logger.debug("... process started.")
        self.started = True
        await self.setup()
        await self.should_stop.wait()

    async def stop(self):
        """Called when the process stop."""
        self.logger.debug("Stopping process...")
        for name, service in tuple(self.services.items()):
            await service.stop()
            del self.services[name]

        self.logger.debug("... process stopped.")
        self.started = False
        await self.cleanup()

    @abstractmethod
    async def setup(self):
        """Called when services have all been started."""
        pass

    @abstractmethod
    async def cleanup(self):
        """Called when the process is about to be stopped."""
        pass

    def start_process(self, process_name):
        """
        Start a task in a separate process.

        This simply is a helper to create processes.  This is most useful
        for the launcher and portal process.  The created process will
        execute in a separate process and synchronization will have to
        be done through the CRUX/host service.

        Args:
            process_name (str): the name of the process to start.

        The name should be the script or executable name without extension.
        If the Python script is frozen (`sys.frozen` set to True), then
        the command is called as is.  In other word, if the process
        name is "portal":

          1.  If not frozen, executes 'python portal.py'.
          2.  If frozen, executes 'portal'.

        """
        # Under Windows, specify a different creation flag
        creationflags = 0x08000000 if os.name == "nt" else 0
        command = f"python {process_name}.py"
        if getattr(sys, "frozen", False):
            command = f"{process_name}.exe"
        self.logger.debug(f"Starting the {process_name!r} process: {command!r}")
        process = Popen(command, creationflags=creationflags)
