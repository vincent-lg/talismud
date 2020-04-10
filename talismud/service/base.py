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

"""Abstract class for TalisMUD services.

A service is a component of the game in charge of a specific functionality.
A service can start one or several asynchronous tasks and run while these
tasks also are running.  Services can have a very short life, but most of
them start with processes and end when these processes end as well.

A service can have sub-services.  These services will be started as the
parent service starts.  However, no isolation is granted between services
and sub-services: a service may call a parent, a parent may call a child.
Services know who their parent, sibblings and children are and they will
use their features shamelessly.  A basic hook system exists to allow
services to "subscribe and react" to given events.  These hooks are not
meant for feature isolation, just speedy communication between services.

Lastly, notice that services are built for asynchronous tasks.  Almost
all their methods are asynchronous.  They can perform many of their
communication on the event loop.  Processes can order services and
organize their behavior, but most services know how to reach a different
service for communication and split responsibilities when it's needed.
To some extent, this gives self-contained code, to the exception of hooks.
Once more, however, feature isolation isn't a goal of this design.

"""

from abc import ABCMeta, abstractmethod
import asyncio
from importlib import import_module
from typing import Coroutine, Tuple

from process.base import Process

class BaseService(metaclass=ABCMeta):

    """Abstract service, from which all services should inherit.

    Class variables:
        name: human-readable name of the service.
        sub_services: a tuple of service names to start as sub-services.

    Methods:
        init: when the service is ready to start.
        setup: when the service has started with its sub-services.
        cleanup: the service is ready to stop, sub-services have stopped.
        register_hook: synchronous method to create a service hook.
        schedule_hook: synchrone method to subscribe a coroutine to a hook.
        call_hook: method to execute a hook with its coroutines.

    Helper methods:
        indented: return an indented message depending on the service depth.

    """

    name: str
    sub_services: Tuple[str] = ()

    def __init__(self, process: Process = None, parent: "BaseService" = None):
        self.started = False
        self.services = {}
        self.process = process
        self.parent = parent
        self.logger = process.logger
        self.hooks = {}

        # Calculate the depth of the service from the process
        # 'depth' of 1 means this is a service of the process. 'depth' of
        # 2 indicates this is a sub-service of the process. 'depth' of 3
        # indicates it's a sub-sub-service and so on.
        self.depth = 1
        while parent:
            self.depth += 1
            parent = parent.parent

    def __repr__(self):
        desc = f"<Service {self.name}, "
        if self.started:
            desc += "running"
        else:
            desc += "not running"

        if self.parent:
            desc += f" with parent {self.parent}"
        desc += ">"
        return desc

    def indented(self, message: str, added_depth: int = 0) -> str:
        """
        Return the message with indentation matching the service depth.

        Args:
            message (str): the message to indent.
            added_depth (int, optional): added depth to the message.

        Four spaces will be inserted before the message for each level of
        depth.  This allows nicer formatting in log messages for instance.

        Return:
            indented_message (str): the indented message.

        """
        depth = self.depth + added_depth
        return depth * 4 * ' ' + message

    async def start(self):
        """
        Start the service asynchronously.

        This method SHOULD NOT be overridden in a subclass, except if
        the starting process has to completely change.  Prefer overriding
        `setup` or `init` which are called by `start`.  Sub-services
        also are started in this method.  If you feel like you really have
        to override 'start', call the parent method with 'super'.

        Order of execution:
            1.  `start` first calls the service's `init` method, which is
                where new attributes should be defined.  You can think of
                `init` as an alternative, asynchronous constructor, though
                this is not entirely true.
            2.  Then sub-services are started (their `start`  method
                is called and awaited).
            3.  Finally the service `setup` method is called.

            In other words, if you override `init`, you can be sure no
            sub-service of this service has been started yet.  However,
            if you override `setup`, you know sub-services have been
            started.  What you will most need depends primarily on when
            you need your code to be executed.

        A last concern arises from the asychronous nature of these
        methoids:  they won't block execution directly, but the result
        of each will be awaited before the next step in the process
        is followed.  If you want to do something that will take
        time to complete, or will need to run in parallel (for instance,
        create a TCP server), then consider using
        `asyncio.create_task` to start a task during the `setup`
        method.  If you do that, capture the task in an attribute so that
        you can cancel it in `cleanup`, if needed.

        """
        sv_type = "service" if self.depth < 2 else "sub-service"
        self.logger.debug(self.indented(f"Starting {sv_type} {self.name}."))
        await self.init()

        # Start the sub-services
        for name in self.sub_services:
            module_name = f"service.{name}"
            module = import_module(module_name)
            cls = getattr(module, "Service")
            service = cls(process=self.process, parent=self)
            self.services[name] = service
            await service.start()

        await self.setup()
        self.logger.debug(self.indented(f"... {sv_type} started."))
        self.started = True

    @abstractmethod
    async def init(self):
        """
        Asynchronously initialize the service.

        This method should be overridden in subclasses.  It is called by
        `start`` before sub-services are created.  It plays the role of
        an asynchronous constructor for the service, and service attributes
        often are created there for consistency.

        """
        pass

    @abstractmethod
    async def setup(self):
        """
        Set the service up.

        This asynchronous method is called by 'start'.  You should override
        it in a subclass to prepare the service when it starts, after
        sub-services have also been started.  Notice that sub-services
        `init` and `setup` method will be called before the parent service
        `setup` method.  However, keep in mind that should sub-services
        create asynchronous tasks (with `asyncio.create_task` for instance),
        there is no guarantee these tasks will be executed after services
        have been setup, unless you put special synchronization means
        into place (using an async queue for instance).

        """
        pass

    async def stop(self):
        """
        Stop the service, waiting for tasks to be cleaned up.

        This method SHOULD NOT be overridden in a subclass, except if
        the stopping process has to completely change.  Prefer overriding
        `cleanup` which is called by `stop`.  Sub-services also are cleaned
        up in this method.  If you feel like you really have to override
        'stop', call the parent method with 'super'.

        """
        sv_type = "service" if self.depth < 2 else "sub-service"
        self.logger.debug(self.indented(f"Stopping {sv_type} {self.name}."))

        # Stop the sub-services
        for name, service in tuple(self.services.items()):
            await service.stop()
            del self.services[name]

        await self.cleanup()
        self.logger.debug(self.indented(f"... {sv_type} stopped."))
        self.started = False

    @abstractmethod
    async def cleanup(self):
        """
        Clean the service up before shutting down.

        This is the opportunity to cancel asynchronous tasks if needed.

        """
        pass

    def register_hook(self, hook: str):
        """Register a new, empty hook."""
        if hook in self.hooks.keys():
            self.logger.warning(f"{self.name}: hook {hook!r} is already declared.")

        self.hooks[hook] = []

    def schedule_hook(self, hook_name: str, coroutine: Coroutine):
        """
        Schedule a coroutine to be called when the hook executes.

        Args:
            hook_name (str): name of the hook.
            coroutine (Coroutine): the coroutine to be called.

        When the hook executes, it calls the coroutines subscribed to
        this hook in the same order they have been sche3duled.

        """
        self.hooks[hook_name].append(coroutine)

    async def call_hook(self, hook_name: str, *args, **kwargs):
        """
        Call the hook asynchronously.

        Args:
            hook_name (str): the hook name.

        Additional positional or keyword arguments will be sent to
        each coroutine when executed.

        This gives an opportunity to processes or services to
        execute specific code when an action occurs.  Hooks must be
        created (registered) beforehand and a call to `schedule_hook`
        from processes or services is required.

        For instance, the `host` service, which is to try and connect
        to the 'CRUX' service, might call a hook when the connection
        has been established.  Other parts of the process can then ask
        to do something when it happens.  In this scenario, the 'host'
        service will:
            Create the empty hook (`register_hook`), probably on setup.
            Call this hook when the connection has been established.
        In order for, say, the process to do something when the host
        is connected, it should schedule a coroutine to be executed
        when the host's hook is called.

        """
        coroutines = self.hooks.get(hook_name)
        if coroutines is None:
            self.logger.warning(
                    f"{self.name}: calling the {hook_name!r} hook, but "
                    "this hook hasn't been registered."
            )

        for coroutine in coroutines:
            try:
                await coroutine(*args, **kwargs)
            except asyncio.CancelledError:
                return
            except Exception:
                self.logger.exception(f"hook {hook_name!r}: an exception occurred while executing a coroutine:")
