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

"""Message of the Day context, displayed when one connects to TalisMUD."""

from context.base import BaseContext

class MOTD(BaseContext):

    """
    Context called when the user first connects to TalisMUD.

    The user will leave this context at once, to enter connection.home.

    """

    text = r"""Welcome to
          *   )           )                   (    (  (
        ` )  /(  (     ( /((        (  (      )\   )\ )\
         ( )(_))))\(   )\())\  (    )\))(  ((((_)(((_)(_)
        (_(_())/((_)\ (_))((_) )\ )((_))\   )\ _ )\)_()_)
        |_   _(_))((_)| |_ (_)_(_/( (()(_)  (_)_\(_) || |
          | | / -_|_-<|  _|| | ' \)) _` |    / _ \ | || |
          |_| \___/__/ \__||_|_||_|\__, |   /_/ \_\|_||_|
                                   |___/
    """

    async def refresh(self):
        """Leave this context at once."""
        await super().refresh()
        await self.move("connection.home")
