"""Public settings.

This is a Python file containing your public game settings.  You can modify
these settings simply by changing their Python value.  If you want to
hide this setting from players (you don't want to show them your password
salt for instance), you can copy the setting from this file, paste it
in "settings/prifvate.py" and update it there.  This change won't appear
in your source tree.

"""

# 1. Game name and general settings
# The game name, probably public.
GAME_NAME = "TalisMUD"

# The game version, can be shown in the Message-Of-The-Day screen if you wish.
GAME_VERSION = "0.0.1"

# The game longer description if you want one, as a multiline string.
GAME_DESCRIPTION = """
This is a cool game, since it's my very own.

But yes, it's based on TalisMUD.  Still, it's my very own.
"""

# 2. Security settings
# Note: password settings that are changed AFTER the first accounts
#       have been created will render these accounts impossible to
#       connect to because their password can't be accessed anymore.  If
#       you change these settings, do it before your create your first
#       accounts, or change them and erase your database altogether
#       to start from fresh.
#       BUT YOU DO NOT HAVE to change these settings as they provide
#       a high degree of security already.

# Algorithm name to use to hash passwords.
# Recommended choices are sha256 and sha512, but you can use something else.
HASH_ALGORITHM = "sha256"

# Salt size
# The salt will be randomly-generated for each password.  It is
# recommended your salt to be at least 16 bytes in length, but it
# can be longer.
SALT_SIZE = 32

# Number of iterations
# To store your password, the algorithm will build a stronger hash
# if you specify a greater number of iterations.  The greater the number,
# the slower it will perform however.  It is recommended to use at least
# 100,000 iterations for a SHA-256 password, so that's the default setting.
HASH_ITERATIONS = 100_000

# Key size
# You don't have to specify a key size as PBKDF2 will choose a size
# for you.  But you can override its decision.  Set to `None` to
# let PBKDF2 decide.
KEY_SIZE = None

# The following settings can be changed afterward.
# Two-letter country code to use for the SSL certificates (US, FR, ES...).
COUNTRY = "FR"

# State/province name for the SSL certificates.
STATE = "None"

# Locality name for the SSL certificates.
LOCALITY = "Paris"

# Organization name for the SSL certificates.
ORGANIZATION = "TalisMUD"

# 3. Network interfaces and ports

# Allow external connections (from the Internet). Note that even if this
# setting is set to True, accessing your game from the Internet will
# be affected by a lot of factors.
# If False, only connections from the local host will be accepted.
PUBLIC_ACCESS = True

# The port users have to connect to if they use a Telnet-like MUD client.
TELNET_PORT = 4000

# The port users have to connect to in order to access your game website.
# Note: changing this setting to 80 or 443 is a bad idea.  Use proxies
# instead.  See the deployment guide.
WEB_PORT = 4001

# The port users have to connect to in order to access the telnet-SSL game.
# A connection to telnet-SSL is identical to telnet, except the connection
# is secured (passwords, in particular, do not travel in plain text on the
# network).  You can set this to None if you don't wish to have a
# telnet-SSL port, but you probably don't have a good reason for doing
# so.  Not all MUD clients support SSL, unfortunately.
TELNET_SSL_PORT = 4003

# 4. Login options
# Minimum length of username (in characters)
MIN_USERNAME = 4

# Forbidden usernames
FORBIDDEN_USERNAMES = ("talismud", "test", "guest", "new")

# Minimum length of password (in characters)
MIN_PASSWORD = 6

# Forbidden character names
FORBIDDEN_CHARACTER_NAMES = FORBIDDEN_USERNAMES

# Starting room for new characters, enter the room barcode (str)
START_ROOM = "begin"

# Room if the character location has been destroyed while she was away
RETURN_ROOM = "begin"

# 5. Display settings
# Preferred encoding for new sessions without a configuration.
# (Individual clients/players can change that setting for their connection.)
DEFAULT_ENCODING = "utf-8"

# 6. Content creation settings
# These settings affect how your builders can work to contribute content
# to TalisMUD.
# Blueprint parser
BLUEPRINT_PARSER = "yaml"

# Blueprint directory to store blueprint files
BLUEPRINT_DIRECTORY = "blueprints"

# Blueprint backup mode
BLUEPRINT_BACKUP = True

# 7. Plugins
# Plugins can add or replace behavior.  Like the rest of the game,
# they're entirely open and can be customized.  Plugins are simple
# directories, found in the "plugins" parent directory.  They
# contain commands (these would replace or extend the list of commands
# in the game), contexts, database entities and other details.
# To activate the features in a plugin, just add it to the below
# setting, which is a tuple of plugin names.  The order in which
# you'll find this tuple is the order in which plugins are loaded,
# therefore, if two plugins replace the 'look' command, keep the
# one you want to replace this command after the other one in the tuple.

# Installed plugins
PLUGINS = (
        "builder",
)
