# TalisMUD - Download, quick start

TalisMUD is a @MU*@ engine, written in Python.  Starting with it is pretty simple, you might not even need Python to run it.

## Windows users

1.  You have two choices at that point:

    * Either [download the archive](https://github.com/vincent-lg/talismud/archive/master.zip).  This archive contains the current source code, the documentation and some scripts to run TalisMUD quickly.
    * If you have [Git](https://git-scm.com), it is recommended to clone the repository.  Go to your desired location and type:

        git clone https://github.com/vincent-lg/talismud.git

    This will create a directory, named "talismud", in which you'll find the source code, documentation and the same scripts to efficiently run TalisMUD.

    > Why is it better to clone the repository, instead of just downloading the archive?

    If you just want to see TalisMUD in action, downloading the archive will be quicker (you don't need to [download and install Git](https://git-scm.com/downloads)), but cloning with Git will allow you to change whatever you want in the code while still seeing new TalisMUD updates and merging them with your code, if you wish.  If you want to read more about this process, head to the [deployment documentation](deploy/index.md), which will explain how to take the most out of TalisMUD and Git.

2.  If you have downloaded TalisMUD in the archive, uncompress it.  Inside you should find a directory named "talismud".  And inside of it, a "src" directory.  Open it.  If you have cloned the repository from Github, just move into the "src" directory.
3.  Open a Windows console.  TalisMUD offers you a graphical tool to manage your game, but to make sure that everything works out, it's best to run the console this one time.  You should be inside the "src" directory.  Enter the command:

        talismud

    At this point you might receive a message like this:

        Preparing to download 34.62 MB from https://github.com/vincent-lg/talismud-build/archive/win32.zip...

    Then you'll see a simple progress bar indicating the file is being downloaded.  This file is TalisMUD Windows build and it's a bit heavy, as you can see.  It doesn't make sense to have it in the source repository, so the `talismud.exe` program will download and extract it the first time.

    > What's inside?

    The Windows build archive is a relatively heavy zip archive with four executables inside, and a lot of frozen Python code.  That's why you don't have to download and install Python, it's already there, frozen in a nice executable (well, in [four nice executables](#four-executables) in our case).  They'll be placed into a `"build"` directory inside your `"src"` directory.  You don't have to create it, it's supposed to work out of the box.  If you're curious, you can open the `"build"` directory and look inside the "win32"` sub-directory.  Spoiler alert: it's not extremely pretty, but you'll find the four executables we'll talk about in [the next section](#four-executables).

    So when you type the command:

        talismud

    It actually runs the "talismud.exe" program inside your "src" folder.  This program will see if the directory "build" exists with a valid Windows build.  If not, it will download it.  And then it will execute the bigger build inside the "build" directory.  So when you type "talismud", it will actually run `build\win32\talismud.exe`.

    > What do you mean by frozen?

    You can think of the Windows build as a glorified "python.exe" version.  The required dependencies are frozen, along with the ability of Python to read your source code.  However, TalisMUD remains in source files.  If you modify them, you will see the changes.

    > I don't want a frozen, or half-frozen, Python.  Can't I install TalisMUD without relying on this build?

    You definitely can and it's not so complicated.  This is discussed in more details in [how to install TalisMUD with Python](install_from_source.md).

3.  If TalisMUD is happy with your system, after some time it should display something like this:

        Download complete successfully.  Now extracting the new build...
        Remove the 'build.zip' file...
        Remove the 'tmp' directory...
        usage: talismud [-h] {start,stop,restart,shell,script,test,command} ...

    This is TalisMUD's way of saying everything worked, the build could be downloaded and run without error.  We'll now see what it all means.

## Four executables

Once installed, TalisMUD should allow you to use four executables.  All of them are in the "src" directory:

* `talismud.exe`: this is our console entry point, where you will type commands.  You might not be used to working in the console, and you don't really need to, but it's important to have the option for different reasons.
* `graphical.exe`: this is our graphical tool.  If you double-click on it, a window should appear to allow you to work with your game.  Both the console and graphical tool offer the same features.
* `game.exe`: this opens the game itself.  You shouldn't have to use it, it's used internally by TalisMUD.  So it's here as a shortcut.  It might be useful to run advanced debugging or performance testing, but these will be scarce.
* `portal.exe`: the portal, frozen into its executable as well.  The [game](#the-game) and [portal](#the-portal) are two processes TalisMUD uses, and you can learn more about them below.  Again, you shouldn't need to call this executable manually, it's automatically called by `talismud.exe` or `graphical.exe`, but it's left as a shortcut when debugging or performance testing.

So out of these four executables, you should only worry about two: the console tool (`talismud.exe`) and the graphical tool (`graphical.exe`).  Using either or both will depend more on how to achieve something, rather than what to achieve.  Some will find a window much more comfortable, some will prefer a console tool.

## Start the game, start the fun!

Enough theories!  Let's start the game to see what it does.  You have two choices to start you game:

*   Through the console: run the command:

        talismud start

    The `talismud.exe` program will run a bit like a Linux Daemon: you need to start it, but it won't stop unless you ask it.  You can close the console after you have received the confirmation from this command.

        Starting the portal ...
        ... portal started.
        Starting the game ...
        ... game started (id=OjoxOjUyNDI1OjA6MA==, ...).

    For the time being, let's ignore this talk about a [portal](#the-portal) and [game](#the-game), you don't really need to understand these processes right now.  If it's your first time running `talismud`, you will also be asked to create an administrator account.  We'll talk about it next, because this also applies to the graphical window.

*   Through the graphical window: double-click on `graphical.exe`.  You should see a window with the "current status", telling you the game isn't running.  Click on the "start" button.  After a few seconds you should see the MUD is running.  Again, if it's your first time running the game, you will be asked to create an administrator account.  You don't have to keep the window open either, you can shut it down.  When you double-click on `graphical.exe`, it will know the game is still running and will tell you so.

Either in the console or graphical window, if you haven't run the game previously (or if there's no administrator in your game), you will be asked to create one.  The administrator is the user that can run administrative commands in your game.  You don't want everyone to be able to do that, so you should choose a username, password (preferably strong password) and optionally an email address (you don't have to specify an email address).  You can create more administrator accounts afterward.

Once this is done, the game should indicate your administrator account has been set up.

While TalisMUD is running, you can connect to your game through a MUD client (like Telnet, TinTin++, MushClient).  To do so, open your favorite client and connect to:

*   Host name: localhost

    (Meaning your own machine.)

*   Port : 4000

If everything goes well, inside your client you should see a welcome message:

    Welcome to
              *   )           )                   (    (  (
            ` )  /(  (     ( /((        (  (      )\   )\ )\
             ( )(_))))\(   )\())\  (    )\))(  ((((_)(((_)(_)
            (_(_())/((_)\ (_))((_) )\ )((_))\   )\ _ )\)_()_)
            |_   _(_))((_)| |_ (_)_(_/( (()(_)  (_)_\(_) || |
              | | / -_|_-<|  _|| | ' \)) _` |    / _ \ | || |
              |_| \___/__/ \__||_|_||_|\__, |   /_/ \_\|_||_|
                                       |___/
    If you already have an account, enter its username.
    Otherwise, type 'new' to create a new account.
    Your username:

This welcome screen can be changed, and easily so, but let's not do it right now.  Let's check your administrator account does exist.  Enter the username you have typed earlier, then press RETURN.  You will be asked for the password.  Enter it.  You'll then see a list of characters to play from.  So far there shouldn't be more than one character in this account, so you can type 1 and then press RETURN.

You now should be inside your game world.  You can type in commands and see the result.  Congratulations!  There's much to be done for this TalisMUD experience to become your very own game, but everything that comes after that should hopefully be fun to do.

While TalisMUD is running, you can also access TalisMUD's website.  Open your favorite browser (Mozilla Firefox, Google Chrome, Microsoft Edge) and connect to http://localhost:4001/ .  This is your game website, and you can, of course, customize it.  That's part of your game experience, after all, and although you don't necessarily have to add a website to your game, it's not a bad idea, especially since TalisMUD offers one.

## Restart the game

When you'll start customizing, either your game or your website, you will probably make modifications in your game code.  This is how it's supposed to happen.  But whatever you've modified won't appear instantly in your current game.  This would be too dangerous.  Instead, you can modify (add or change Python files) in your code, but TalisMUD will keep on running on its current version until you tell it to restart.

The nice thing is, restarting TalisMUD won't disconnect any of your players.  It will create a short moment during which players can't type in commands, usually one second, and then the game will be up and running again.

To restart your game, you have several options:

-   Inside your game, with an administrator account, you can type the command:

        restart

    Players won't have access to this command and you should make sure not a lot of people have access to it.  It might only stop the game for a second, but if players are actively engaged in play and don't see it coming, they might grumble, especially if it happens every minute.  So try to make sure this restart command isn't open to a lot of people.

        > restart

        Restarting the game ...
        ... game restarted!

    And then you can go on.  This is unvaluable to fix bugs, add commands, fix small errors.  It's not common to completely shutdown the game and start it all over again.

-   In the console, you can achieve the same thing by running:

        talismud restart

    And if everything goes according to plans, you should see something like:

        Game stopping ...
        ... game stopped.
        Start game ...
        ... game started (id=OjoxOjUyNDg5OjA6MA==).

-   From the graphical window, you can also click on the "restart" button.  The messages will be similar.

> How does it work?  It feels like magic!

This is a stark contrast to older MUD games that need to completely shutdown (disconnect everyone) to start over again.  This is accomplished through the [portal](#the portal) and [game](#the game) processes which will be discussed later.

## Stop the game completely

Sometimes it's necessary to stop the game altogether.  That might not be frequent in production, but that's probably going to happen a lot while developing on your local machine.  Again you have three options:

-   From the game, and an administrator account, type the command:

        shutdown

    The game will stop without confirmation and disconnect everyone.

-   In the console, enter the command:

        talismud stop

-   In the graphical window, click on the "stop" button.

These commands will both stop the [game](#the-game) and [portal](#the-portal) processes.

## Two processes

It's time to see what the portal and game processes are, at least to have a basic understanding of the principle allowing TalisMUD to restart without disconnecting anyone.

### The portal

The portal is one of TalisMUD's processes.  The role of the portal is to listen to connections.  The portal doesn't do much but listens and forwards commands to [the game process](#the-game).  On the other hand, it does have an important role: players connect to the portal through different ports.  The portal doesn't contain your game at all (no command, context or web pages).  When the game is restarted, the portal just waits, patiently, for the game to be back.  Since players are connected to the portal, they're not disconnected and experience just a slight lag.

### The game

The game process contains, well, your game: your commands, your contexts, your web pages, your settings and everything else that makes up your game.  The only thing the game process doesn't contain is a mechanism to listen to new connections on ports, this role is devoted to the portal.

So the portal sits on ports, it's a gateway through which all traffic must go.  When the game restarts, the portal just waits for it to be back and then sends the commands again.

## Up and running?  What next?

Hopefully, TalisMUD is now running on your machine.  What can you do next?  A lot of things, but where to start?

The next step will depend on you and your skills, or rather, what you want to learn:

*   I want to create things but not code.

    The good news is that you can potentially create everything (including commands) without coding.  Of course, you will have to write scripts to do so, which is a bit like coding, but that will be more simple and you will learn little by little through a custom tutorial.  In any case, you should head to the [builder tutorial](building/tutorial).  If you prefer to have a larger and more structured documentation, you could head to the [builder documentation](building) itself, which will let you choose what topic you want to investigate first.

*   I want to code, know how things work and modify them as early as I can.

    In this case, head to the [developer tutorial](dev/tutorial), a step-by-step guide on things to do to customize TalisMUD.  If you're already familiar with this tutorial, or with part of TalisMUD, you might prefer to check out [the developer documentation](dev) which lists all topics you can learn.  It's somewhat more arid and might get you dizzy, but it's detailed and pragmatic.

## TalisMUD won't start, what's wrong?

Unfortunately, it's not completely impossible TalisMUD won't start, especially if you tweak the portal or game.  In this context it might be hard to know what's wrong, though not impossible.

### The start process freezes

One common problem is in the start process.  Say you have typed in the console:

    talismud start

It tells you it's trying to start the portal... and will wait... and will wait... and will finally fail, telling you it couldn't.  Or it will start the portal just fine but will hang when starting the game.

TalisMUD will try to tell you what's wrong, but it can't always know.  The first thing is to head over to the log files.

Inside your "src" directory, you should see a sub-directory called "logs".  Inside should be several log files, that is files describing what has happened.  With luck they will contain your error.  Try to open either "portal.log" (containing the errors of the portal process) or "game.log" (containing the errors of the game process).  Look at the bottom of the file.  It's likely you'll find your error there with a full traceback.

Of course, a traceback is somewhat useless when you don't know the process used by TalisMUD, but the final line might help you understand the problem.  If not, don't hesitate to [contact a TalisMUD developer](contact.html).

If you don't even see a log file, it's possible that either process couldn't even log the error.  It's unusual, but not unheard of.  In this case you should run them separately.  (You see why these executables exist now!)

Go to the console and start your game, not through TalisMUD commands, but through the game executable:

    game

If everything goes well, the game should tell you in short lines that it's able to run.  If not, you will find a full traceback.

You can stop the game with `CTRL + C`.  If you think your error might come from the portal, run it in the console as well:

    portal

Again, if the portal can connect, it will tell you.  Otherwise you will see a nice traceback.

TalisMUD will try to tell you if an error occurred, in particular, when you restart the game.  But it's not a guarantee of course.

Still stuck?  It might be time to reach out.  Please [contact the project developers](contact.html) and we'll try to help.  And update this page, if that's a question we often get!
