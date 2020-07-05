from command import Command

class Look(Command):

    """
    Look around.

    Usage:
        look

    """

    async def run(self, args):
        """Run the command."""
        room = self.character.location
        if room is None:
            await self.msg("Well, you don't seem to be anywhere...")

        await self.msg(room.look(self.character))
