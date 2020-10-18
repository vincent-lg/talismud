# Scripting in TalisMUD

TalisMUD offers a rich and flexible environment.  As a builder of your game world, you will across a lot of relatively static data: adding rooms, adding objects, adding characters, perhaps adding vehicles or other information.  But there are some times when you'll want to add more flexibility to your world and just creating data won't help.

A script is a way to add dynamic behavior linked to one object, or a set of objects.  You can think ot it as a very simple program that will affect how a command behaves for certain rooms, objects, characters or whatever you game offers  You will find more examples and explanations in the following section.

## Why is scripting useful?

The goal of a script is to add dynamism to your static world content.  The reasons why this is useful, however, may vary depending on your usage.  So we'll look at it from two different perspectives.

### I'm a builder, why not ask coders to do it?

Scripting can seem too complicated and remote to builders: the main role of a b uilder, for a MUD anyway, is to write content.  A builder can create maps and try to add new sections to the game world.  This task would seem limited by developers at first glance.

Say you want to add a quest to your zone for instance.  A quest, as understood here, is a set of tasks a player character can complete to obtain some benefits.  A task as understood by a builder is a mission with a clear purpose, often shaped by a story.  An NPC could "give a quest", that is, present the player character with a given need and ask for help.  Other NPCs could be involved in the story and, usually, what to do can involve rooms or objects.  A builder whose only role is to write content will contact a developer at this point: "I need this quest, could you make it happen?" That would require a lot of work and the builder could only direct the initial process.  The developer may not be a writer, and may not respect the story as it was first imagined by the builder.  And when it's in place, changes requested by the builder would require more involvement from developers.

This separation of responsibilities isn't necessarily the right approach.  If buildeders could do it themselves, creating quests or other special behaviors, they could offer consistent content with a high level of flexibility.

A script is a simplistic program with a lightweight syntax that anyone can understand, with or without a programming background.  Builders will find it intuitive to use and simple to implement, while doing more advanced tasks is by no mean impossible.

### I'm a developer, why not code?

If your game is maintained by developers, you might wonder about why it's necessary to allow builders to script.  So let's consider it from a structural viewpoint.

Imagine you have a "push" command in your game, allowing you to push various things in your rooms.  You could code such a command in Python, using the command system.  Eleemnts to be pushed in a room would be special objects, perhaps, or other static content.  That works right?

But what would happen if you try to push one?  How to explain what to do?  You could decide to have a "Pushable" class?

```python
class Pushable:

    """Class to represent something that can be pushed in the room."""

    name = Str()

    def action(self, character):
        """The character pushes this item."""
        pass
```

So you would need to subclass `Pushable` each time you want to add something you can push in your room.

```python
class Chair(Pushable):

    """A chair in a given room."""

    name = "chair"

    def action(self, character):
        """When the character pushes the chair."""
        character.msg("You push the chair and it topples over to reveal... something.")
```

And then you would need to add your items to each room with a chair that's meant to be pushed.  You might already see the problem: you would need to add a class for each action.  That's understandable for a single item, but if your game has 5.000 of them, you would need 5.000 subclasses.  Not ideal.

Another approach would be to add an event to each object: "push".  A builder (or developer) could create a "push" script and associate it with different objects.  When the command "push" is called, it will call the "push" script of this object.

You wouldn't need to create any additional classes to handle a specific behavior.  Instead you would just need to add an event to all object scripts and associate a script to each object you want to push.  The script will contain the behavior.

## But what is it, really?

A script is just some code in its own language you would connect to object in different circumstances.

A script ressembles Python, but it's not exactly Python.  Here's a small example.  This script could be linked to a heavy object that can be "pushed" in the room:
    Room: begin
    Object: heavy chest
    Event name: push
    Script content:

        # character is a variable in the script containing the
        # character pushing this object.
        if character.strength > 5:
            character.msg("You push the chest and it reveals a rapdoor!")
            character.room.exits.add("down", "cellar")
        else:
            character.msg("You push... but the chest won't move!")
        end

This is a relatively simple example, but it might not be intuitive to builders at first sight, so let's decompose it:

1. This script is linked to an object, "heavy chest", in the room "begin".  A script is usually linked with an object, though it can be linked to a room, character or vehicle.
2. The script is connected to the event "push".  This event will be called when the player character enters "push" command with an argument in this room.  Like "push heavy chest" in this context.
3. The script contains a simple behavior: it should do something different depending on the character's strength:
   - Line 1:2: this is just a comment, to explain `character` doesn't come from nowhere.
   - Line 3: beginning of an "if" block.  In this case, we check that the player character that pushed our heavy chest has strength equal or above 5.
   - Line 4: if so, we display a message telling the player character it could move the chest and that doing so makes a trapdoor appear.
   - Line 5: and we create an exit.  The way to create an exit might sound a bit strange, but this will be explained in more details in the [tutorial](./tutorial.md).
   - Line 6: otherwise (if the character has less than 5 in strength).
   - Line 7: we display another message.  No trapdoor appear.  No exit is created.

This is a simplistic script, obviously.  In practice you would need to check for more information.  But that should illustrate how scripts work.