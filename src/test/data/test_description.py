"""Test the behavir of object with a description."""

from test.base import BaseTest

class TestDescription(BaseTest):

    def test_set(self):
        """Set a description."""
        room = self.create_room()
        self.assertIsNone(room.description.get(None))

        # Set the description
        room.description.set("A fake description")
        self.assertEqual(room.description.get().text, "A fake description")

    def test_clear(self):
        """Set a description, then clear it."""
        room = self.create_room()

        # Set the description
        room.description.set("A description")
        self.assertIsNotNone(room.description.get(None))

        # Then clear it
        room.description.clear()
        self.assertIsNone(room.description.get(None))
