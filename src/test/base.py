"""Base test for TalisMUD tests.

It creates an in-memory database for each test, so they run in independent
environments.

"""

from itertools import count
import unittest

from pony.orm import db_session

from data.base import db
from data.cache import CACHED
from data.decorators.lazy_property import LazyPropertyDescriptor

# Bind to a temporary database
db.bind(provider="sqlite", filename=":memory:")
db.generate_mapping(create_tables=True)

# Constants
ID_CHAR = count(1)
ROOM_TITLE = count(1)
ROOM_BARCODE = count(1)

class BaseTest(unittest.TestCase):

    """Base class for TalisMUD unittests."""

    def setUp(self):
        """Called before each test method."""
        db.create_tables()
        db_session._enter()

    def tearDown(self):
        """Called after the test method."""
        # Reset lazy properties
        for entity in db.entities.values():
            for key in dir(entity):
                value = getattr(entity, key)
                if isinstance(value, LazyPropertyDescriptor):
                    value.memory.clear()

        # Clean up the cached objects
        for cached in CACHED.values():
            cached.clear()

        # End the database session
        db_session.__exit__()
        db.drop_all_tables(with_all_data=True)

    def create_character(self):
        """Create a character."""
        return db.Character()

    def create_instance(self, cls):
        """Create and return an instance of the specified class."""
        cls_name = cls.__name__
        return getattr(self, f"create_{cls_name.lower()}")()

    def create_room(self, title=None, barcode=None):
        """Create and return a room."""
        title = title or f"room {next(ROOM_TITLE)}"
        barcode = barcode or f"code {next(ROOM_BARCODE)}"
        return db.Room(title=title, barcode=barcode)
