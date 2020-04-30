from command import Command, CommandArgs

class Reload(Command):

    """
    Command to reload the game.

    Usage:
        reload

    """

    args = CommandArgs()

    async def run(self, args):
        """Run the command."""
        await self.session.msg_portal("restart_game")
