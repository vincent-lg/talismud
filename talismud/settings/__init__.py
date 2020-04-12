"""Setting package.

All settings can be either public or private.  Public settings are
committed and, should your game be open-source, everyone will see them.
However, you can override these public settings with private settings:
the private setting file (settings/private.py) will be ignored and not
committed.  Your changes to it won't appear in your source, unless you
want them to be.

> What to do to change settings?

First, explore the "public/settings.py" file.  See the current settings.
If you see something you want to change:

1.  If it can be shown to your players, simply change it in the public
    file.  For instance, you don't want to hide your game name, more
    likely than not.  So just update "settings/public.py" with your
    modifications.  Be aware, these are still Python files and
    should contain correct Python syntax.  The setting keys are capitalized
    like Python constants should be.
2.  If you see a setting you want to change but you don't want this change
    to be visible by your players, then copy the setting in your
    "settings/private.py" file and paste the setting key and value.
    And change the value.  Your "settings/private.py" file should contain
    the same settings as the "settings/public.py" file, but they will
    override the public settings if any conflict.

When TalisMUD needs a setting, it will first look into the private
settingsds ("settings/private.py").  If it doesn't find it, it will
look in the public settings ("settings/public.py").  If your game
isn't open-source and you have no desire to show it to anyone,
you don't really need to worry about the difference.  Be aware,
however, that this system allows you to open your code while keeping
some information hidden from users.  And open-source should be a good
choice, whether for a game or another project.

"""

# Import the public settings file first
from settings.public import *

# Imports the private settings.  They will override the public settings.
from settings.private import *
