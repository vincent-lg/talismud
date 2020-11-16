import traceback
from command import Command, CommandArgs

class Say(Command):

    """
    Say something in your location.

    Usage:
        say <message>

    """

    args = CommandArgs()
    args.add_argument("text", dest="message")

    async def run(self, message):
        """Run the command."""
        await self.msg(f"You say: {message}")
