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

"""Services for the TalisMUD game, separated in several processes.

TalisMUD runs with a set of services at different levels.  Their goal
can be to add features or maintain high access to the game.  Not all services
are mandatory.  The following explanation focuses on services that
TalisMUD needs to work.

TalisMUD is packaged inside a broader process and service, the game.
This service, meant to to run in its own process, is responsible for much
of the game handling: interpreting commands, communicating with the
database, handling the virtual world are all tasks of the game service.

Users don't connect to the game directly however.  Another service, called
the portal service, is to be started with the game and not be stopped
if possible.  The portal service listens on public ports and handles
connections.  When a player wishes to play to TalisMUD, she will
connect to the portal.  The portal will communicate with the game,
indicating that it has received a new connection and asking what it should
do.  If the player sends a command, the portal informs the game about
this command and waits for its answer.

The portal and game runs in different processes: this means that the game
itself can restart.  If so, users won't be disconnected because they're
on the poortal service.  The portal service will lose the ability
to communicate with the game while the game restarts.  When the game
has restarted, the portal reestablishes connection and sends whatever
commands it had received while the game was down.  This simple
hierarchy allows to restart the game for any code modification (like
fixing of a bug) without disconnecting a single user.  This will
create a downtime of a few seconds during which users won't be able
to play, but this won't result in any loss of data or connection.

Other services, like the webserver or Telnet SSL server can be added and
they will most likely run on the game or portal process, depending on
their need.  The portal and game process communicate with a loose
Asynchronous Messaging Process (both processes can send commands and receive
answers).

See the modules:
    game: contains the game service.
    portal: contains the portal service.
    telnet: contains the telnet sub-service, running on the game service.
    web: contains the web sub-service, running on the game service.

"""
