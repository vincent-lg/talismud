"""Private game settings, invisible to your players.

Even if your game is open-source (as I personally encourage), players
won't see this setting file, and you can safely modify it to your
liking.  You could include game-related sensitive data you don't want
anyone to see.  Notice, however, that if you don't use Git as a Version
Control System, you will have to check how to ignore modifications
to this file in your own VCS.

To change settings and make them private, browse your
"settings/public.py" file.  See any setting you want to make private?
Then copy the line or lines to the "settings/private.py" file and modify
them here.

>   Always keep the default settings as public.  Otherwise, someone wishing
    to run your game, but not having your private settings (because you
    don't share them) would receive errors if he doesn't have default
    settings to rely on.

If possible, keep the same organization as the "settings/public.py"
file.  This will help you organize your settings.

"""

# 1. Game name and general settings
GAME_NAME = "TalisMUD"
