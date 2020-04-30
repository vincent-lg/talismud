from command import Command, CommandArgs

class Shutdown(Command):

    """
    Command to shutdown the game.

    Usage:
        shutdown

    """

    args = CommandArgs()

    async def run(self, args):
        """Run the command."""
        await self.session.msg_portal("stop_portal")
