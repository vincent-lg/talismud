"""Test the behavir of object with registered names."""

from data.base import db
from test.base import BaseTest

class TestNames(BaseTest):

    def test_split(self):
        """Split a name."""
        character = self.create_character()
        names = character.names.split("this is a green mouse")

        # Just make sure all individual words and some combination
        # are present.
        self.assertIn("this", names)
        self.assertIn("is", names)
        self.assertIn("a", names)
        self.assertIn("green", names)
        self.assertIn("mouse", names)
        self.assertIn("this is", names)
        self.assertIn("a green", names)
        self.assertIn("a green mouse", names)
        self.assertIn("this is a green mouse", names)

    def test_search_simple(self):
        """Test to search through names."""
        character1 = self.create_character()
        character2 = self.create_character()

        # Register a different name for each character
        character1.names.register("a tiny green mouse")
        character2.names.register("A huge blue elephant")

        # Search 'tiny', should yield character1
        result = character1.names.search("tiny")
        self.assertIn(character1, result)
        self.assertNotIn(character2, result)

        # Search 'elephant', should yield character2
        result = character1.names.search("elephant")
        self.assertNotIn(character1, result)
        self.assertIn(character2, result)

        # Search 'a', should yield character1 and character2
        result = character1.names.search("a")
        self.assertIn(character1, result)
        self.assertIn(character2, result)

        # Search 'a tiny', should yield character1
        result = character1.names.search("a tiny")
        self.assertIn(character1, result)
        self.assertNotIn(character2, result)

        # Search 'huge bl', should yield character2
        result = character1.names.search("huge bl")
        self.assertNotIn(character1, result)
        self.assertIn(character2, result)

        # Search 'orange', should yield an empty list
        result = character1.names.search("orange")
        self.assertNotIn(character1, result)
        self.assertNotIn(character2, result)

        # Search 'iny', should yield an empty list
        # Note: 'iny' is the end of 'tiny', but no word
        # in either names begins with 'iny', so that should fail.
        result = character1.names.search("iny")
        self.assertNotIn(character1, result)
        self.assertNotIn(character2, result)

    def test_search_extra_spaces(self):
        """Test to search through namest with extra spaces."""
        character1 = self.create_character()
        character2 = self.create_character()

        # Register a different name for each character
        character1.names.register(" a blue mouse")
        character2.names.register("A GREEN-AND-BLUE lizard")

        # Search 'mouse', should yield character1
        result = character1.names.search("mouse")
        self.assertIn(character1, result)
        self.assertNotIn(character2, result)

        # Search 'green', should yield character2
        result = character1.names.search("green")
        self.assertNotIn(character1, result)
        self.assertIn(character2, result)

        # Search 'blue', should yield character1 and character2
        result = character1.names.search("blue")
        self.assertIn(character1, result)
        self.assertIn(character2, result)

        # Search 'green and  blue', should yield character2
        result = character1.names.search("green and  blue")
        self.assertNotIn(character1, result)
        self.assertIn(character2, result)

    def test_search_with_punctuation(self):
        """Test to search through names with punctuation."""
        character1 = self.create_character()
        character2 = self.create_character()

        # Register a different name for each character
        character1.names.register("a tiny, green mouse")
        character2.names.register("A huge, REALLY HUGE. blue whale")

        # Search 'tiny', should yield character1
        result = character1.names.search("tiny")
        self.assertIn(character1, result)
        self.assertNotIn(character2, result)

        # Search 'tiny green', should yield character1
        # (The comma should be removed.)
        result = character1.names.search("tiny green")
        self.assertIn(character1, result)
        self.assertNotIn(character2, result)

        # Search 'huge blue', should yield character2
        # (The dot should be removed.)
        result = character1.names.search("huge blue")
        self.assertNotIn(character1, result)
        self.assertIn(character2, result)

    def test_search_order(self):
        """test the search ordering."""
        room = self.create_room()
        character4 = self.create_character()
        character1 = self.create_character()
        character5 = self.create_character()
        character2 = self.create_character()
        character3 = self.create_character()

        # Move all characters in the room, following an order
        character1.location = room
        character2.location = room
        character3.location = room
        character4.location = room
        character5.location = room

        # Register a different name for each character
        character1.names.register("a blue mouse")
        character2.names.register("a brown rabbit")
        character3.names.register("a white kangaroo")
        character4.names.register("a blue whale")
        character5.names.register("a white-and-blue elephant")

        # search 'white', this should yield character3 and character5
        result = character1.names.search("white")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], character3)
        self.assertEqual(result[1], character5)

        # search 'blue', this should yield [character1, character4, character5]
        result = character1.names.search("blue")
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], character1)
        self.assertEqual(result[1], character4)
        self.assertEqual(result[2], character5)

        # search 'a', this should yield all characters

        # Move character3, then try again
        character3.location = character1
        character3.location = room
        result = character1.names.search("a")
        self.assertEqual(len(result), 5)
        self.assertEqual(result[0], character1)
        self.assertEqual(result[1], character2)
        self.assertEqual(result[2], character4)
        self.assertEqual(result[3], character5)
        self.assertEqual(result[4], character3)

    def test_conflict_with_tags(self):
        """Make sure there is no conflict with tags."""
        character = self.create_character()

        # Add a name and a tag
        character.names.register("a tiny fish")
        character.tags.add("blue")

        # Make sure 'blue' is not a name
        self.assertEqual(character.names.search("blue"), [])

        # Make sure 'fish' isn't a tag
        self.assertFalse("fish" in character.tags)
