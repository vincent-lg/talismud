"""Test the behavir of objects with permissions."""

from data.base import db
from data.search import search_permission
from test.base import BaseTest

SUPPORTED = (db.Character, )

class TestPermissions(BaseTest):

    def test_add(self):
        """Add permissions to the objects suppoorting it."""
        for supported in SUPPORTED:
            cls_name = supported.__name__
            with self.subTest(msg=f"in class {cls_name}"):
                tested = self.create_instance(supported)
                self.assertEqual(len(tested.permissions), 0)
                self.assertFalse(tested.permissions.has('inside'))

                # Add a permission without category
                tested.permissions.add("inside")

                # Check that 'inside' is tagged on tested
                self.assertEqual(len(tested.permissions), 1)
                self.assertTrue('inside' in tested.permissions)
                self.assertTrue(tested.permissions.has('inside'))

                # Create the same permission on this object.
                # Nothing should happen.
                tested.permissions.add("inside")

                # Check that 'inside' is tagged on tested
                self.assertEqual(len(tested.permissions), 1)
                self.assertTrue('inside' in tested.permissions)
                self.assertTrue(tested.permissions.has('inside'))

                # Remove this tag.
                tested.permissions.remove("inside")

                # Check that 'inside' is not tagged on tested anymore.
                self.assertEqual(len(tested.permissions), 0)
                self.assertFalse('inside' in tested.permissions)
                self.assertFalse(tested.permissions.has('inside'))


    def test_search(self):
        """Test to search through permissions."""
        for supported in SUPPORTED:
            cls_name = supported.__name__
            with self.subTest(msg=f"in class {cls_name}"):
                obj1 = self.create_instance(supported)
                obj2 = self.create_instance(supported)
                obj3 = self.create_instance(supported)

                # Add permissions to each object, with or without category
                obj1.permissions.add("timed")
                obj1.permissions.add("blue", category="color")
                obj2.permissions.add("blue", category="mood")
                obj3.permissions.add("timed")
                obj3.permissions.add("content", category="mood")

                # Search 'blue', no specific category.
                # Should yield obj1 and obj2.
                result = search_permission("blue")
                self.assertIn(obj1, result)
                self.assertIn(obj2, result)
                self.assertNotIn(obj3, result)

                # Search 'timed', no specific category.
                # Should yield obj1 and obj3.
                result = search_permission("timed")
                self.assertIn(obj1, result)
                self.assertNotIn(obj2, result)
                self.assertIn(obj3, result)

                # Search 'blue' of category 'mood'.
                # Should only yield obj2.
                result = search_permission("blue", category="mood")
                self.assertNotIn(obj1, result)
                self.assertIn(obj2, result)
                self.assertNotIn(obj3, result)

                # Search in the 'mood' category, no specific name.
                # Should yield obj2 and obj3.
                result = search_permission(category="mood")
                self.assertNotIn(obj1, result)
                self.assertIn(obj2, result)
                self.assertIn(obj3, result)

    def test_conflict_with_tags(self):
        """Make sure there is no conflict with tags."""
        character = self.create_character()

        # Add a permission and a tag
        character.permissions.add("admin")
        character.tags.add("blue")

        # Make sure 'blue' is not a permission
        self.assertEqual(character.permissions.search("blue"), [])

        # Make sure 'admin' isn't a tag
        self.assertFalse("admin" in character.tags)
