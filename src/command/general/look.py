from command import Command

class Look(Command):

    """
    Look around.

    Usage:
        look

    """

    alias = "l"
    args = Command.new_parser()
    search = args.add_argument("search", dest="target", optional=True)
    search.search_in = (lambda character: character.location
            and character.location.contents or None)

    async def run(self, target=None):
        """Run the command."""
        if target:
            await self.msg("looking at {target}.")
            return

        room = self.character.location
        if room is None:
            await self.msg("Well, you don't seem to be anywhere...")

        await self.msg(room.look(self.character))
