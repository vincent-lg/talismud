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
# if you specify a greater number of iteration.  The greater the number,
# the slower it will perform however.  It is recommended to use at least
# 100,000 iterations for a SHA-256 password, so that's the default setting.
HASH_ITERATIONS = 100_000

# Key size
# You don't have to specify a key size as PBKDF2 will choose a size
# for you.  But you can override its decision.  Set to `None` to
# let PBKDF2 decide.
KEY_SIZE = None

# 3. Network interfaces and ports

# Allow external connections (from the Internet). Note that even if this
# setting is set to True, accessing your game from the Internet will
# be affected by a lot of factors.
# If False, only connections from the local host will be accepted.
PUBLIC_ACCESS = True

# Ports players have to connect to if they use a Telnet-like MUD client.
TELNET_PORT = 4000

# Ports users have to connect to in order to access your game website.
# Note: changing this setting to 80 or 443 is a bad idea.  Use proxies
# instead.  See the deployment guide.
WEB_PORT = 4001

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
