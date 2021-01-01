# Tutorial on commands in TalisMUD

Adding a new command in TalisMUD is extremely simple.  This tutorial will show you how it is done, and how to do more with command arguments.

## Add a basic command

To add a command in TalisMUD, it's necessary to create a Python file.  This Python file should be inside the "command" directory or a sub-directory (we'll talk about grouping commands later).

We are going to try and create a command, "roll", aimed to roll a die on a virtual table and display the result.  Sounds simple?  Luckily it's not much harder in TalisMUD.

First, create a file.  For this example, I suggest creating a "command/general/roll.py" file.  So open the "command" directory (in TalisMUD's "src" directory), open the "general" sub-directory and create a new file named "roll.py".

> Hold on, I thought commands were in the "command" directory, not the "general" directory"?

When TalisMUD searches for commands, it explores sub-directories inside the "command" directory too.  In theory you could create other directories inside "general" and put your file in it, but let's not complicate things quite yet.

Inside your "command/general/roll.py" file, paste in the following code:

```python
from command import Command

class Roll(Command):

    """
    Roll a die.

    Usage:
        roll

    This command allows you to roll a basic die and get the result.

    """

    async def run(self):
        """Run the command."""
        await self.msg("Well, at least, you hit the 'roll' command.")
```

Did I say "simple"?  Well, one thing you'll have to admit, it's not too long.  But before we dive into the code, let's see what this code does.

Save your file, reload the game (either by running `talismud restart` in the console or by typing `reload` in your MUD client).

Then you should be able to enter `roll` in your MUD client and see the message:

    Well, at least, you hit the 'roll' command.

Fantastic!  A bit too simple.  Let's talk about the code.

### Code explained

Our commands is composed of 17 lines, no less, and most of it is just blank lines and comments.  Still, there are some things that might puzzle you, so let's review line by line:

* Line 1: it's just an `import` statement, to bring `Command` into scope.  If you're not familiar with `import` statements, it's highly recommended to learn a bit more about them before going on.
* Line 3 creates a class in Python.  The name of the class follows Python naming convention (it has a capital letter at the beginning), but it's the same as the file name otherwise.  It's your command name.  Although it can be changed, commands assume the name of the class is the name of the command (although the uppercase letters are converted to lowercase).  This command inherits from `Command`,  which is our abstract command class (all your commands should inherit from `Command`).
* Line 5 to 13: that's just a docstring describing what your class (what your command) does.  Regarding commands, this text is shown to your players, in the command help system.  So this little docstring is important, lets your player know how to use your command.
* Line 15: the definition of our first and only method for this command.  Its name is `run`.  You're probably familiar with this `def run(self)` part, but you might be less familiar with the `async` keyword before `def`.  This lets Python know it is an asynchronous method.  It's not the time and place to write a course about `asyncio`, and if you don't know it, just add this keyword.  Know that since we use the `await` keyword in the method, we need `async` before the definition.  Otherwise, Python complains.
* Line 17: finally we send a message to the character.  We call `self.msg`, which is an instance method on the command.  The command will forward our message to the character, the character to the connected session, and the session to your MUD client.  Didn't get that part?  Don't worry, just know `self.msg(...)` sends a message to the player's MUD client.  We use `await` before calling `self.msg`.  This is a requirement because the message can take some time in being sent.  Not long, mind you, but other players can enter commands without blocking everyone while we wait for the message to be sent.

So that's done!  But you might be a little confused with `async` and `await`, so we'll over-simplify: `await` means "take your time and come back whenever you're ready".  It's necessary to `await` when sending a message to the player.  So we always, always place `await` before `self.msg(...)`.  If you don't, you might not notice a problem, but you won't receive the message.

As for `async`, it is necessary to place it before `def` in methods that use `await`.

Is it better?  Perhaps not.  Let's see more examples!

We were supposed to have our 'roll' command roll a die... but it just sends a message.  Time to change that!

We'll simply use `random` to generate a semi-random number, between 1 and 6.  You can update you "roll.py" file as follows:

```python
from random import randint

from command import Command

class Roll(Command):

    """
    Roll a die.

    Usage:
        roll

    This command allows you to roll a basic die and get the result.

    """

    async def run(self):
        """Run the command."""
        number = randint(1, 6)
        await self.msg(f"You roll a die on the table... and get a {number}!")
```

Again, save this file and reload your game.  Enter the "roll" command.  Here's what I obtain:

```
> roll

You roll a die on the table... and get a 3!

> roll

You roll a die on the table... and get a 4!

> roll

You roll a die on the table... and get a 1!

> roll

You roll a die on the table... and get a 6!
```

Well, that's better!

In terms of code, our file didn't change that much.  We add an `import` to `random.randint`, which we use to generate semi-random numbers.  The only other modification is in our `run` method where we create a variable holding our semi-random number, then sends it to the character running the command.

> What's that `f"You roll a die on the table... and get a {number}!"` thing?

This is a formatted string, a f-string for short.  This notation was introduced in Python 3.6 and allows to display variables directly in strings, like we just did.  You will probably get used to the notation very quickly.  Of course, you can use `str.format`, or even `%-style` formatting, although you really shouldn't.

To recap:

1. Adding a command in TalisMUD requires adding a file.
2. The Python file usually is composed of the command name and the `.py` extension.  If the command name isn't a proper Python name, better to change the Python module name and rename the command in it (we'll see how later).
3. Inside the Python module should be a class that inherits from `Command`.
4. The command help can be found in the class docstring, usually just below the class definition.
5. The code that is executed when the command runs is contained in the `run` method.  It's an asynchronous method, place `async` in front of the `def` keyword.

Common questions:

> Can I define several commands in one file?

You should avoid doing it.  TalisMUD can work with that setup, but it will make your life a bit more complicated down the line.  Better keep one class per file.

> My command doesn't appear... and thus doesn't work.  Why can't TalisMUD find it?

See the section on [troubleshooting commands](#troubleshooting) below.

## Command data

Our command class is quite empty at the time.  Although we won't need these attributes in this tutorial, except for the command arguments (see [the section on command arguments][#command-arguments]), it might be useful to know them.

Class attributes are defined in the class itself, usually just below the class docsting.  For instance:

```python
class Roll(Command):

    """
    Roll a die.

    Usage:
        roll

    This command allows you to roll a basic die and get the result.

    """

    name = "roll"
```

Here we have changed the name of the command (kind of, because it already had the name "roll").  Let's see the available command data defined in attributes:

- `name`: this allows to change the command name.  By default, this is the same as the class name, but lowercased.  Here we have defined a class `Roll`, so the command name is `roll`.  If you're not happy with the default name, you can change it here.  This is also useful if you want to create a command, but the command name isn't a valid Python name.  In this case, feel free to choose a more Python-appropriate class name and rename the command by providing the true command name in this attribute.
- `category`: this represents the command category.  Specify the category as a string.  Commands will be grouped in the help by categories.  So its usage is mostly for the help command.
- `permissions`: the command permissions.  Most of the time, they are quite simple.  They're empty by default, meaning anyone can execute this command.  You can set a group (like `"admin"`) instead.  You can also override the `can_run` method to have even more control over who can run this command, but usually changing the command permission is quite enough.
- `args:`: the command arguments.  We'll talk about that in more details in [the section about command arguments](#command-arguments).
- `seps`: the command separators.  Usually, a command name and its argument are separated by a space.  For instance, if the player enters "look tree", we assume that "look" is the command name, and "tree" is the command argument.  This can be changed, however, separators can be something other than a space... and you can even have several separators.  You can set the `seps` class attribute with a string of available separators (by default, it's just `" "`).
- `alias`: the command alias, or aliases.  A command can have one or more aliases.  An alias is just a way (a shorter way, usually) to reach the command.  For instance, the "look" command has an alias "l", so a player can type "l" or "l tree" and the "look" command will be called.  Specify the alias, if only one, as a string, like `alias = "l"`, or as a tuple, if more than one, like `alias = ("l", "ls")`.
- `layer`: this is a string describing the command layer.  This concept is discussed in more details in its own tutorial, see [command layers](layer.md).

All these class attributes have default values, so just use them if you want to change the command's behavior.

## Command arguments

It's not unusual for a command to have arguments.  Command arguments allow players to be more specific about what they want to do.  For instance, if you create a "say" command, it would be hard to use without allowing players to specify what to say:

    say hello everyone!

Arguments are usually specified after the command name, separated by a space.  TalisMUD offers a way to handle arguments without repeating the same code again and again.

To keep this connected to a useful feature, let's improve on our "roll" command.  We would like to support a mandatory argument: the number of sides of the die.  For instance, if you type "roll 6", we'll return the result of a six-sided die.

### Example of a number as argument

We'll work with our `args` class attribute.  You might not remember it, but that's one of the class attributes you can customize in your command.  For the time being, we'll examine it independently of our command code to avoid confusing anyone and we'll see the end result afterward.

First we need to create the argument parser.  The parser is responsible for "parsing" the argument, that is to extract the proper arguments from the text following the command name.

```python
args = Command.new_parser()
```

So far, nothing too complicated.  We create a new argument parser, by calling the `new_parser` method on the `Command` class.  This will return a new parser.  And we're going to use it to add arguments.

> Don't place it in anything but the class variable named `args`, otherwise TalisMUD won't find it.

This is an empty parser, identical to what you would have obtained if your command hadn't specified any.  Not very useful!  It will become more useful if we add an argument:

```python
args = Command.new_parser()
args.add_argument("number", dest="sides")
```

The second line here is more complicated.  We call `add_argument`, which is a method on our parser.  The first argument to `add_argument` is the argument type: you'll see in the [full documentation on arguments[(../args.md) the provided argument types and what they can do.  For the time being, just know `"number"` is a type that accepts a number.  Nothing else.

Doesn't sound impressive?

Maybe not.  Well, let's test it!  Edit you "roll.py" file to add this argument.  Better to copy and paste the following code to be sure you make the proper changes (we'll comeback to it just below):

```python
from random import randint

from command import Command

class Roll(Command):

    """
    Roll a die.

    Usage:
        roll <sides>

    This command allows you to roll a basic die and get the result.

    """

    args = Command.new_parser()
    args.add_argument("number", dest="sides")

    async def run(self, sides):
        """Run the command."""
        number = randint(1, sides)
        await self.msg(
                f"You roll a {sides}-sided die on the table... "
                f"and get a {number}!"
        )
```

More lines have changed than what was expected, but you'll see the changes are quite simple:

*   Line 17-18: these lines were added.  Line 17 adds an empty parser, line 18 adds a `"number"` argument to our parser.  That's just what you saw before, but indented and placed where it should be.
*   Line 20: our method definition for `run` has changed a little.  Now you see:

        async def run(self, sides):

    We have another argument, named `sides`.  This will be the number entered  by the player.

*   Line 22 and 23: these lines have changed a bit, because we now have the number of sides as argument, so both the random call and the message change a bit.  Notice that the message starting at line 23 is actually spread on several lines.  This is useful when we have a long line, like now.

Ho, and don't forget to edit your command help, when you'll have players to use it.

You might not understand everything that happens, but before describing it in more details, let's see the effect.  Save your "roll.py" file, reload your game and try to call this command:

```
> roll

You should specify a number.

> roll 6

You roll a 6-sided die on the table... and get a 6!

> roll 10

You roll a 10-sided die on the table... and get a 7!

> roll 12

You roll a 12-sided die on the table... and get a 7!

> roll that

'that' isn't a valid number.

> roll maybe not

'maybe' isn't a valid number.

```

As you can see, a number is expected... and not providing any, or pvoiding a wrong number results in an error.  The error message can be customized, and that will be described in more details in the [section about argument options](#argument-options), but what we already have allows us to know that if `run` is called, a valid number is sent to it.

Of course, "a valid number" can have different meanings too.  These all are options on this argument, but before we see them, let's first talk about what happens in terms of code.

1. A player enters "roll 12".
2. The list of command is browsed.  TalisMUD understands the player refers to the "roll" command.  At the same time, the command arguments are written (the part that is not a command name for TalisMUD).  Here, it's just `"12"`.
3. Then TalisMUD calls on the command parser.  The parser has one argument registered: "number" (with "dest" of `"sides"`).
4. The number argument looks at the arguments to parse.  It considers `"12"` (still as a string) and gathers it's a valid number.  So it writes `12` (as an `int`) into the parsed command arguments.
5. The parsed arguments are sent as keyword arguments to `run`, so if the player sends "roll 12", the command will be called like this: `command.run(sides=12)`.

That's a simplification, of course, and you'll see that some of these steps have been really shortened, but what matters is that a successfully-parsed argument becomes a keyword argument (perhaps of a different type).

> Why is it good?

First, it allows you to write your commands without repeating the code to parse a string into an `int` and saves you from some common errors.  When you write 100 commands that need numbers as arguments, that's a lot of line of code that you don't need to repeat.

Second, command arguments can be chained, so you can have a complex command with several arguments in no time.  We'll see how to do that now.

### Chaining arguments

Command arguments wouldn't be so neat if one couldn't chain them.  By "chaining" here, understand that a command can have several arguments.  Their order, their mandatory state or their default value, their error messages... everything can be customized.

So let's update our "roll" command to require two numbers:

*   The number of rolls.
*   The number of sides.

So rolling three six-sided dice could produce anything between 3 and 18 (3 being the number of dice, 18 being 6 times 3, the maximum random number of individual dice).

So we'll need to accept something like this:

    roll 3 6

... and that will roll a six-sided die three times.

The code doesn't look so difficult to write, you already have everything.  Just remember to place the number of rolls and the number of sides in different arguments (with a different `dest`), otherwise things could get complicated.

```python
from random import randint

from command import Command

class Roll(Command):

    """
    Roll a die.

    Usage:
        roll <times> <sides>

    This command allows you to roll a basic die and get the result.

    """

    args = Command.new_parser()
    args.add_argument("number", dest="rolls")
    args.add_argument("number", dest="sides")

    async def run(self, rolls, sides):
        """Run the command."""
        number = randint(rolls, rolls * sides)
        await self.msg(
                f"You roll a {sides}-sided dice {rolls} times on the table... "
                f"and get a {number}!"
        )
```

You shouldn't be too surprised at these modifications.  In short, we add a new argument to our argument parser.  We add another keyword argument in our `run` method.  And we (slightly) modify the message to be sent to the user, as well as the calculation to generate a random number.

Let's see it in action:

```
> roll

You should specify a number.

> roll 5

You should specify a number.

> roll 3 6

You roll a 6-sided dice 3 times on the table... and get a 17!

> roll 2 ok

'ok' isn't a valid number.
```

That works pretty well... the only thing that could be improved is our error messages.  If we don't specify any number, or only one number, the message is identical, although the reason is different.  Luckily we can change that through argument options, let's see it now!

### Argument options

It is possible to customize the individual arguments through options.  Options are just attributes on individual arguments.  Let's keep the same example of our "roll" command, trying to improve our error messages.

Error messages are usually prefixed with `msg_`.  In this case, if you look at [the options of the number command argument](../args.md#number), you should find `msg_mandatory`, which is sent when the player didn't specify any argument.  So let's modify it for our first argument, you'll see how simple it is:

```python
...
    args = Command.new_parser()
    rolls = args.add_argument("number", dest="rolls")
    rolls.msg_mandatory = "Specify the number of times you want to roll."
    args.add_argument("number", dest="sides")

...
```

We just catch the return of `add_argument` in a variable (`rolls` here) which contains our argument, and then modify its `msg_mandatory` attribute.

Save, reload your game and try again:

```
> roll

Specify the number of times you want to roll.

> roll 3

You should specify a number.
```

A bit better, but our second argument still has its default message, which doesn't really help.

Never mind, let's edit it:

```python
...
    args = Command.new_parser()
    rolls = args.add_argument("number", dest="rolls")
    rolls.msg_mandatory = "Specify the number of times you want to roll."
    sides = args.add_argument("number", dest="sides")
    sides.msg_mandatory = (
            "You also should specify the number of sides on your dice."
    )
...
```

Basically the same thing.  Since the message is a bit longer, I've used a notation to spread the definition on several lines.  You can use `\` at the end of your line to achieve the same, I personally prefer breaking long strings with parents.

Again, save and reload, and try it:

```
> roll

Specify the number of times you want to roll.

> roll 3

You also should specify the number of sides on your dice.

> roll 3 6

You roll a 6-sided dice 3 times on the table... and get a 3!
```

Error messages are more helpful and combined with your command help, players should figure out to use your command.  Don't hesitate to be more explicit (to remind the player about your command syntax for instance), it's not a waste of time to create a good interface, albeit in a textual game.

You'll find other options on arguments, different options depending on the argument type.  You might have noticed, for instance, we can't enter negative numbers:

```
> roll -8 2

'-8' isn't a valid number.
```

Even 0 isn't accepted!  That can be configured.  By default, number arguments have a minimum set on 0, you cannot enter anything less than 1.  But that can be changed.  You can also set a maximum limit.  And change both error messages to be more explicit.  That's all options you can easily set.

> How do I know which options are available?

Head to [the documentation on command arguments](../args.md).  In it you'll find the list of supported command arguments and their options.

## Grouping commands in directories

It is possible to group commands, and even recommended to do so.  Command grouping allows to specify a common category, a permission or a command layer.  We won't talk about command layers here, that's a bit more advanced, but let's look at category and permissions.

If you remember, both the command category and permissions can be specified as attributes on the command class.  If you look into an administrator command (like `py`), you might be a bit surprised though:

    talismud command py

... will display:

    Layer   Command  Category        Permissions  Python path
    static  py       Admin commands  admin        command.admin.py.Py

So it has a different category (`Admin commands`) and different permissions (`admin`).

But if you open the `command/admin/py.py` file, you won't find this information:

```python
class Py(Command):

    """
    Command to execute Python code.

    Usage:
        py <Python code to execute>

    """

    alias = "python"
    args = Command.new_parser()
    args.add_argument("text", dest="code")

    async def run(self, code):
        # ...
```

Well, there's no `category` or `permissions` attribute, where do this information come from?

The answer is that commands can be grouped.  When Python doesn't find the `category` class attribute, it looks in the module for a `CATEGORY` top-level variable.  If it doesn't find it, it will look in the parent package for a top-level variable named `CATEGORY`.  And if it doesn't find it, it will go to the parent package, and so on, until it finds something.

In our case, there's no `category` class attribute.  There's no `CATEGORY` in the module itself, but if you look in the parent package (that is, the file `command/admin/__init__.py`), you'll find it.

```python
CATEGORY = "Admin commands"
```

> Why is it a good thing?

With the category defined in the parent package, you can add commands in the "admin" directory and all of them will be in the same category, unless you change individual categories (you still have this option).  This is good because you can easily change the category of all admin commands in this example for instance.

And the same applies to two other details:

* Permissions: permissions are specified on an individual basis by modifying the `permissions` class attribute of a command.  But again, if the command doesn't have this class attribute, TalisMUD will try to find a `PERMISSIONS` top-level variable in the module, then in the parent package, then in the grandparent package, and so on.  In our example, all commands under the "admin" package will inherit the same permissions (`"admin"`).  You don't have to be careful about permissions and you can easily change them, if you want.
* Command layers: command layers are defined in the `layer` class variable.  If not found, a `LAYER` top-level variable will be searched in the module, the parent package, the grandparent package and so on until this information is found.

We haven't played with command layers in this tutorial.  This topic is a bit more advanced and its use case might be less common, but there's a full [tutorial about command layers](layer.md) you can go to if you want more information on this topic.

## ... and much more

This tutorial, however long, was an introduction to commands.  Many other topics are related to commands, or explore their usage in more details.  So if you find a question that's not answered here, check the list below to see if your topic is there... and if not, don't hesitate to [contact TalisMUD's developers](../../contact.html).

*   How to store data in commands?

    This can be answered in two ways: if you want to store some information for this command and the player using it, you should use the [command storage](command-storage.md).  If, on the other hand, you want to store information related to the player, and not linked to the command, it might be time to learn about the [database and how it works](database.md).

*   How to pause for a delay in commands?

    Often, you'll find you need to pause a command for some time.  Learn how to [handle delays in commands](command-delay.md) to do that.

*   How can a command open a menu?

    The concept of menus in text-based games can refer to several things.  However, the most common use case is a question asked to the player, where she might have to choose in a choice.  Menus can be much more complicated, they can be used by builders to create for instance.  In TalisMUD, menus are described in a tool (simply called `Menu` for that matter).  Read the following tutorial [to learn how menus can be created and used in commands](command-menus.md).

*   Can a command display soeme kind of table?

    TalisMUD relies on another tool, called `table`, to display information in a text-based representation.  Although it doesn't sound that hard to code that yourself, the provided tool handles cell wrapping (if text is too big for a column), coloring (if text contains color codes) and different kinds of border, along with other features.  Read [this tutorial on tables](table.md) for more information.

## Troubleshooting

With flexibility comes some risks: sometimes we work on a command and it's not even added.  Sometimes our command does fail and we don't know why.  This section gives guidance over how to debug in both these situations.

### Where is my command?

TalisMUD has a policy to know which file it should load when trying to find commands.  But it also offers a tool to help you see what the loaded commands are... and where they can conflict.

Open a command-line in TalisMUD's "src" directory.  To see current commands, you can use the "command" sub-command of the "talismud" program.  So either type in the command:

    talismud command

Or, if you've installed Python and the relevant libraries (which is advisable), you can type:

    python talismud.py command

In both cases, it should display something like this:

    Layer   Number of commands  Category
    static                   7  {Multiple}

This is not really useful at this point, you might now be familiar with the concept of command layers.  With no argument TalisMUD will group commands by layers.  For the time being, you can assume that your command is in the "static" layer, we talk about [command layers](layer.md) in another tutorial.

You can type in a filter to the command.  The filter can be a command name, a layer name or a command Python path.  And you can type several filters at once.  For instance, to see what the "static" layer contains, you might do something like:

    talismud command static

... or, if you have Python and dependencies:

    python talismud.py command static

This time, you'll see a different and more helpful (but more crowded) table:

    Layer   Command   Category          Permissions  Python path
    static  look      General commands  {Everyone}   command.general.look.Look
    static  py        Admin commands    admin        command.admin.py.Py
    static  quit      General commands  {Everyone}   command.general.quit.Quit
    static  reload    Admin commands    admin        command.admin.reload.Reload
    static  roll      General commands  {Everyone}   command.general.roll.Roll
    static  say       General commands  {Everyone}   command.general.say.Say
    static  shutdown  Admin commands    admin        command.admin.shutdown.Shutdown

In this table you'll find 5 columns:

* The [command layer](layer.md).
* The command name.
* The command category.
* The command permissions (`{Everyone}` means that there's no specific permission on the command).
* The command's Python path, which will tell you where the command is located.

When using this command, keep in mind that it will not start the game, nor try to connect to it if it's already on.  It will instead load the commands as the game should do it, and will print the table.  This is much quicker, but it also means that, should the game be already loaded, if you've forgotten to reload it, it's quite possible the `talimsud command static` shows you a command you don't have in your game.  Remember to reload your game.

> I still can't find my command.  It's not in the table.

There are a couple of "simple" things to check.  TalisMUD applies its logic to know which command to load... and which one to ignore.

#### Check the file path

First of all, check that Python can access your Python file.  It means that all your path should be valid Python.  If your path contains characters like `-`, or `+` for instance, Python won't be able to import it and will just ignore the file.  If you are unsure of what is a valid Python pat, check [this tutorial on valid identifiers in Python](https://www.programiz.com/python-programming/keywords-identifier).  Keep in mind that accented letters are somewhat tolerated in Python names now (so you can definitely create a variable named `vérité`) but in directory names, encoding might be an issue you don't want to face.  Keep it simple and short and only use ASCII letters (if possible, only lowercase) in your directory names, or your file names.

Take a look at the "roll" command we've created above: first, notice it's inside the "command" directory.  Python files outside this directory (except inside of a [plugin](plugin.md)) will not be loaded.  The sub-package (and sub-directory) is called "general".  This is valid.  The module name is called "roll.py", which is a proper Python module name (the Python name becomes "roll" without the ".py" extension).  And the class name is "Roll", which is also valid.

#### Module names starting with an underscore are ignored

TalisMUD will skip over module names that begin with an underscore.  This can be a way to "hide" or "disable" a command while you're working on it.  So `roll.py` could contain a command, but `_roll.py` will be skipped.

#### Time to debug more

If your Python path seems correct to you but Python still doesn't load, you can use the `talismud command` to go even deeper.  If you specify the full Python path, TalisMUD will attempt to show you what happens with your command.

So let's assume you have a command `command.general.roll.Roll` like in the previous example.  You have modified it and you don't see it anymore.  You can try to debug it in more details:

    talismud command command.general.roll.Roll

... or, with Python installed and configured:

    python talismud.py command command.general.roll.Roll

This will attempt to load this command and try to guess what's wrong with it.

First let's see a success message:

    Try to import this module: 'command.general.roll'
    Roll is a subclass of the Command class, as it should be.
    Name   : roll            Category   : General commands          Layer: static
    Aliases: {No alias}      Permissions: {Everyone}
    This command has properly been loaded into its layer.

This is an all-clear message... almost.  But it can fail at various point in the process:

1. It could fail loading your module, because of a `SyntaxError` exception for instance.  In this case, it will tell you so.
2. It could load your module but fail to find your command.  In this case it will tell you so.
3. It could find your command class just fine, but have trouble finding the command name and command layer.  Watch out for this message, because it might be overlooked: if you see a name of `"{UNSET}"`, it means the command loader didn't work on your command at all.  If the previous steps have worked but the name is unset, it probably means the command loader has decided to not load your command, probably due to its name.  Don't just fix this error by providing the `name` class attribute.  This might show a greater issue and providing a `name` won't necessarily fix it.
4. It might load the command and find its name and other information, but tell you the command name is already in use in this command layer.

Two commands can't have the same name in the same command layer.  In this case, one of them will replace the other.  TalisMUD will help to let you understand which command overrides which one.

To test this situation, I've changed the name of the "roll" command to "look".  "look" is a default command, so the name is not free.  Upon inspection, I find that the former "roll" command is loaded just fine, but when TalisMUD tries to find the other "look" command, it fails and tells y so:

    > talismud command command.general.look.Look
    Try to import this module: 'command.general.look'
    Look is a subclass of the Command class, as it should be.
    Name   : look            Category   : General commands          Layer: static
    Aliases: l               Permissions: {Everyone}
    Inside the static command layer, another command has the name look.
    Therefore, command.general.roll.Roll replaces command.general.look.Look.

This message is quite explicit, and you will only run into trouble if you have more than two commands with the same name, as debugging which command overrides which might be a bit of a problem.  In this case, it might be better to specify the command name as an argument to `talismud command`, like `talimsud command look`, to see which command is loaded, and then debug the other commands.

### My command fails when run

Assuming your command has properly been loaded, it might still fail when run.  Why?  Well, your `run` method might have an issue.  By default, if you are running an admin character (like the one created at the beginning of your adventure with TalisMUD), you're sent the command traceback to debug in peace.  It actually helps you to debug quickly and the usual approach is:

1. Test your command.
2. Fix the error in the file.
3. Save and reload.
4. Test again, repeat.

But there are times when you won't have this information.  Sometimes, it happens because the command seemed to work fine, but when you open it to your players, they find bugs.

Help, it doesn't work!

What to do?  The first reflex is to open the log file.  Commands are logged in the "src/logs/commands.log" file.  In it you'll find the result of a command if it fails without informing the player.  This file also contains the list of commands that were loaded, so it's an alternative to the `talismud command ...` tool.

### Conclusion

Troubleshooting your new command might be complicated, but you have a lot of tools to find the culprit, and fix it.

- The `talismud command` tool: this tool allows you to study loaded commands and obtain more information about replaced commands.
- "src/logs/commands.log": this log file contains information about failed commands, especially commands that failed at runtime.

Your log file might sound like a dangerous thing, a potential breach in privacy.  TalisMUD goes to a lot of trouble to avoid writing sensitive information in this file.  If it fails, that's even more reason to keep it accessible only to you and to avoid exploiting its data, except in emergencies.

Still stuck?  It might be time to reach out.  Please [contact the project developers](../../contact.html) and we'll try to help.  And update this page, if that's a question we often get!
