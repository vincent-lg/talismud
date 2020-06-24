"""Test the behavir of objects with locations."""

from itertools import cycle

from data.base import db
from test.base import BaseTest

class TestLocation(BaseTest):

    def test_moving_character(self):
        """Move a character inside and outside of a room."""
        character = db.Character(name="test")
        room1 = db.Room(title="here", barcode="1")
        self.assertIsNone(character.location)
        self.assertEqual(room1.contents, [])

        # Move che character in the room
        character.location = room1
        self.assertIs(character.location, room1)

        # Check that the room contents contains the character
        self.assertEqual(room1.contents, [character])

        # Move the character in a different room
        room2 = db.Room(title="there", barcode="2")
        self.assertEqual(room2.contents, [])
        character.location = room2
        self.assertIs(character.location, room2)
        self.assertEqual(room1.contents, [])
        self.assertEqual(room2.contents, [character])

        # Finally move the character outside of any room
        character.location = None
        self.assertIsNone(character.location)
        self.assertEqual(room1.contents, [])
        self.assertEqual(room2.contents, [])

    def test_order(self):
        """Test that the ordering in content is accurate."""
        rooms = []
        characters = []

        for i in range(5):
            rooms.append(db.Room(title=f"here_{i}", barcode=str(i)))

        for i in range(20):
            characters.append(db.Character(name=f"character_{i}"))

        # Move characters in rooms
        for character, room in zip(characters, cycle(rooms)):
            character.location = room

        for i, room in enumerate(rooms):
            present = [character for pos, character in enumerate(
                    characters) if pos % 5 == i]
            self.assertEqual(room.contents, present)

    def test_recursion(self):
        """Test the recursion exception when moving inconsistently."""
        character1 = db.Character(name="test")
        character2 = db.Character(name="test2")
        character2.location = character1

        # Moving character1 into character1 should definitely not work
        with self.assertRaises(RecursionError):
            character1.location = character1
        self.assertIsNone(character1.location)

        with self.assertRaises(RecursionError):
            character1.location = character2 # Should be fobidden
        self.assertIsNone(character1.location)

        # Now try to create several objects and a more complicated loop
        room1 = db.Room(title="There", barcode="1")
        room2 = db.Room(title="Somewhere else", barcode="2")
        character2.location = character1
        character1.location = room2
        room2.location = room1

        # room1 contains room2 contains character1 contains character2
        # So moving room1 in character2 should now fail
        with self.assertRaises(RecursionError):
            room1.location = character2
        self.assertIsNone(room1.location)
