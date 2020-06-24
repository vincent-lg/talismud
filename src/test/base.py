"""Base test for TalisMUD tests.

It creates an in-memory database for each test, so they run in independent
environments.

"""

import unittest

from pony.orm import db_session

from data.base import db
from data.properties import LazyPropertyDescriptor

# Bind to a temporary database
db.bind(provider="sqlite", filename=":memory:")
db.generate_mapping(create_tables=True)

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
        db_session.__exit__()
        db.drop_all_tables(with_all_data=True)
