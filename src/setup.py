import distutils
import opcode
import os
import shutil

from cx_Freeze import setup, Executable

talismud = Executable(
    script="talismud.py",
)

game = Executable(
    script="game.py",
)

portal = Executable(
    script="portal.py",
)

graphical = Executable(
    script="graphical.py",
    base="Win32GUI",
)

distutils_path = os.path.join(os.path.dirname(opcode.__file__), 'distutils')
includefiles = [
    (distutils_path, 'lib/distutils'),
    # The 'pubsub' package has to be copied from the virtual environment
    #(os.path.join(os.environ["VIRTUAL_ENV"], 'lib', 'site-packages', 'pubsub', 'utils'), 'lib/pubsub/utils'),
]

setup(
    name = "TalisMUD",
    version = "0.2",
    description = "The TalisMUD frozen executables.",
    options = {'build_exe': {
            "include_files": includefiles,
            "excludes": ["_gtkagg", "_tkagg", "bsddb", "distutils", "curses",
                    "numpy", "pywin.debugger", "pywin.debugger.dbgcon",
                    "pywin.dialogs", "tcl", "Tkconstants", "Tkinter"],
            "packages": [
                    "aiohttp", "aiohttp_session.cookie_storage",
                    "async_timeout", "beautifultable", "bui",
                    "Cheetah.DummyTransaction", "Cheetah.Template",
                    "cryptography", "ctypes.wintypes",
                    "logbook", "pony.orm.dbproviders.sqlite",
                    "pubsub.pub", "yaml",
            ],
            #"namespace_packages": ["zope.interface"],
    }},
    executables = [game, graphical, portal, talismud]
)
