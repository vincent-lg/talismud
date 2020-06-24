from command import Command

class Quit(Command):

    """
    Quit the game.

    Usage:
        quit

    """

    async def run(self, args):
        """Run the command."""
        await self.msg("See you soon!")
        await self.session.msg_portal("disconnect_session",
                dict(session_id=self.session.uuid))
