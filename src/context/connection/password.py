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

"""Account password context."""

from context.session_context import SessionContext

class Password(SessionContext):

    """Context to enter the account's password."""

    prompt = "Your password:"
    text = """
        Enter your accoun't password.
    """

    async def greet(self) -> str:
        """Greet the user."""
        account = self.session.options["account"]
        if account.options.get("wrong_password"):
            return "Please wait, you can't retry your password just yet."
        else:
            return await super().greet()

    async def input(self, password: str):
        """Check the account's password."""
        account = self.session.options.get("account")
        if account is None:
            await self.msg("A problem occurred, please try logging in again.")
            await self.move("account.home")
            return

        if account.options.get("wrong_password"):
            await self.msg(
                    "Please wait, you can't retry your password just yet."
            )
            return

        if account.is_correct_password(password):
            await self.msg("Correct password!")
            _ = account.options.pop("wrong_password", None)
            self.session.account = account
            await self.move("connection.players")
        else:
            account.options["wrong_password"] = True
            await self.msg(
                    "Incorrect password.  Please try again in 3 seconds."
            )
            self.call_in(3, self.allow_new_password, account)

    async def allow_new_password(self, account):
        """Allow to enter a new password."""
        _ = account.options.pop("wrong_password", None)
        await self.refresh()
