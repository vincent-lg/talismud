from random import randint

from command import Command

class Roll(Command):

    """
    Roll a die.

    Usage:
        roll

    This command allows you to roll a basic die and get the result.

    """

    args = Command.new_parser()
    rolls = args.add_argument("number", dest="rolls")
    rolls.msg_mandatory = "Specify the number of times you want to roll."
    sides = args.add_argument("number", dest="sides")
    sides.msg_mandatory = (
            "You also should specify the number of sides on your dice."
    )

    async def run(self, rolls, sides):
        """Run the command."""
        number = randint(rolls, rolls * sides)
        await self.msg(
                f"You roll a {sides}-sided dice {rolls} times on the table... "
                f"and get a {number}!"
        )
        old_number = self.db.get("number", 0)
        await self.msg(f"Old number: {self.db.number if old_number else 'not set'}")
        self.db.number = number
