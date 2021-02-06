from collections import defaultdict

from command import Command
from command.layer import filter_can_run, COMMANDS_BY_LAYERS
from tools.list import ListView

class Help(Command):

    """
    Provide help on a command.

    Usage:
        help (command name)

    This command allows you to obtain help.  Use this command without
    argument to see the list of available commands.  You can also ask
    for specific help on a command, providing the command name
    as argument:
      help look

    """

    args = Command.new_parser()
    args.add_argument("text", dest="name", optional=True)

    async def run(self, name):
        """Run the command."""
        commands = COMMANDS_BY_LAYERS["static"]
        if (character := self.character):
            commands = filter_can_run(commands, character)

        if name:
            command = commands.get(name)
            if command is None:
                await self.msg(f"Cannot find this command: '{name}'.")
            else:
                lines = (
                        f"={'-' * 20} Help on '{command.name}' {'-' * 20}=",
                        command.get_help(self.character),
                )
                await self.msg("\n".join(lines))
        else:
            view = ListView(orientation=ListView.HORIZONTAL)
            view.items.indent_width = 4
            categories = defaultdict(list)
            for command in commands.values():
                categories[command.category].append(command)

            for category, commands in sorted(categories.items()):
                view.add_section(category, [command.name
                        for command in commands])

            await self.msg(view.render())
