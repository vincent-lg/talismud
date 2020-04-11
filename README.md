# TalisMUD

A MUD engine written in Python.

## Installation

You should consider downloading the TalisMUD package without installing it like a library with `pip`.

Just curious?  Then download the source code with executables: [ZIP archive](https://github.com/vincent-lg/talismud/archive/master.zip)

> I'm serious, I want to deploy your tool and create my game with it.

Then clone this repository on Github and make your changes in your public or private repository.

    git clone https://github.com/vincent-lg/talismud.git

> Why is it better to clone rather than download?

If you clone the repository, you can make your own changes to it.  But if I happen to fix a bug in the source you can still benefit from it through a simple merge.  You'll lose this ability when downloading the archive.

## Ready to test, what should I do?

If you're on Windows, you're lucky.  In the "talismud" directory you'll find three executables.  Click on the "talismud.exe" file.  A window will open telling you the game isn't running.  You can click on start and try things out.

But if you're not on Windows, don't worry too much.  You will need Python 3.8 and install the dependencies in "requirements.txt".  Then you can just:

    python3.8 talismud.py

## I don't want an ugly Window, I want a console tool

Both the executable "talismud.exe" and the Python script "talismud.py" are shortcuts to a window which you don't have to use.  If you just want to start the game without opening a GUI:

    talismud.exe start

(OR)

    python3.8 talismud.py start

You can use the `start`, `restart` and `stop` commands.  TalisMUD will behave like a daemon of sort.

## My very own game, not yours.  How to change things?

Well, it's both simple and tricky.  Simple because the game is written in Python and you can just modify the Python files.  Tricky because... well... you have to write Python scripts.  TalisMUD will help you as much as possible in making your job easy and fun, but it can't remove the fact that you'll have to develop, if only a little, should you want your own game.

What's the advantages then, you'd ask?

1. TalisMUD will take care of the low-level and uglier aspects, letting you focus on what you want: creating a fun game.  It will enable you to quickly create both a good gameplay and excellent stories.  All you need to shine are ideas.
2. Even if you're on Windows and running using the executables, should you happen to make a modification to one of the Python files, they'll be taken into account.  You don't have to "compile" or even "build" the executable again.  Think of it as a Python executable with everything you'll need to work in your game, a Python executable that remains the important ability to read Python source files.
3. Found a bug in your game?  Don't panic!  You can restart the game without losing any connection.  Your players will experience a very brief (say one second) lag during which their commands will be stored for later.  In this second, TalisMUD will shutdown the game and restart it.  You can modify the source code, fix a bug or whatever, your modifications will appear after this restart.  And no one will be disconnected.  Talking about a great playing experience.

## Okay... perhaps I want to try.  Where to begin?

