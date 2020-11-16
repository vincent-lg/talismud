"""Test the behavir of object with attributes."""

from data.base import db
from data.search import search_tag
from test.base import BaseTest

SUPPORTED = (db.Character, )

class TestTags(BaseTest):

    def test_add(self):
        """Add tags to the objects suppoorting it."""
        for supported in SUPPORTED:
            cls_name = supported.__name__
            with self.subTest(msg=f"in class {cls_name}"):
                tested = self.create_instance(supported)
                self.assertEqual(len(tested.tags), 0)
                self.assertFalse(tested.tags.has('inside'))

                # Add a tag without category
                tested.tags.add("inside")

                # Check that 'inside' is tagged on tested
                self.assertEqual(len(tested.tags), 1)
                self.assertTrue('inside' in tested.tags)
                self.assertTrue(tested.tags.has('inside'))

                # Create the same tag on this object.  Nothing should happen.
                tested.tags.add("inside")

                # Check that 'inside' is tagged on tested
                self.assertEqual(len(tested.tags), 1)
                self.assertTrue('inside' in tested.tags)
                self.assertTrue(tested.tags.has('inside'))

                # Remove this tag.
                tested.tags.remove("inside")

                # Check that 'inside' is not tagged on tested anymore.
                self.assertEqual(len(tested.tags), 0)
                self.assertFalse('inside' in tested.tags)
                self.assertFalse(tested.tags.has('inside'))


    def test_add_with_category(self):
        """Add a tag with a specific category."""
        for supported in SUPPORTED:
            cls_name = supported.__name__
            with self.subTest(msg=f"in class {cls_name}"):
                tested = self.create_instance(supported)
                self.assertEqual(len(tested.tags), 0)
                self.assertFalse(tested.tags.has('hidden', category='auto'))

                # Add a tag with category
                tested.tags.add('hidden', category='auto')

                # Check that 'hidden' is tagged on tested
                self.assertEqual(len(tested.tags), 1)
                self.assertTrue('hidden' in tested.tags)
                self.assertTrue(tested.tags.has('hidden', category='auto'))

                # Create the same tag on this object.  Nothing should happen.
                tested.tags.add('hidden', category='auto')

                # Check that 'hidden' is tagged on tested
                self.assertEqual(len(tested.tags), 1)
                self.assertTrue('hidden' in tested.tags)
                self.assertTrue(tested.tags.has('hidden', category='auto'))

    def test_add_two_categories(self):
        """Add two tags of the same name, but different category."""
        for supported in SUPPORTED:
            cls_name = supported.__name__
            with self.subTest(msg=f"in class {cls_name}"):
                tested = self.create_instance(supported)

                # Add the 'tag1' tag with category 'cat1'
                tested.tags.add('tag1', category='cat1')

                # Check that the tag has been added
                self.assertEqual(len(tested.tags), 1)
                self.assertTrue('tag1' in tested.tags)
                self.assertTrue(tested.tags.has('tag1', category='cat1'))

                # Add the 'tag1' tag with category 'cat2'
                tested.tags.add('tag1', category='cat2')

                # Check that both tags exist without conflict.
                self.assertEqual(len(tested.tags), 2)
                self.assertTrue('tag1' in tested.tags)
                self.assertTrue(tested.tags.has('tag1', category='cat1'))
                self.assertTrue(tested.tags.has('tag1', category='cat2'))

                # Remove the second tag, the first one should still exist.
                tested.tags.remove('tag1', category='cat2')
                self.assertEqual(len(tested.tags), 1)
                self.assertTrue('tag1' in tested.tags)
                self.assertTrue(tested.tags.has('tag1', category='cat1'))

                # ... but tag1[cat2] shouldn't exist
                self.assertFalse(tested.tags.has('tag1', category='cat2'))

    def test_search(self):
        """Test to search through tags."""
        for supported in SUPPORTED:
            cls_name = supported.__name__
            with self.subTest(msg=f"in class {cls_name}"):
                obj1 = self.create_instance(supported)
                obj2 = self.create_instance(supported)
                obj3 = self.create_instance(supported)

                # Add tags to each object, with or without category
                obj1.tags.add("timed")
                obj1.tags.add("blue", category="color")
                obj2.tags.add("blue", category="mood")
                obj3.tags.add("timed")
                obj3.tags.add("content", category="mood")

                # Search 'blue', no specific category.
                # Should yield obj1 and obj2.
                result = search_tag("blue")
                self.assertIn(obj1, result)
                self.assertIn(obj2, result)
                self.assertNotIn(obj3, result)

                # Search 'timed', no specific category.
                # Should yield obj1 and obj3.
                result = search_tag("timed")
                self.assertIn(obj1, result)
                self.assertNotIn(obj2, result)
                self.assertIn(obj3, result)

                # Search 'blue' of category 'mood'.
                # Should only yield obj2.
                result = search_tag("blue", category="mood")
                self.assertNotIn(obj1, result)
                self.assertIn(obj2, result)
                self.assertNotIn(obj3, result)

                # Search in the mood' category, no specific name.
                # Should yield obj2 and obj3.
                result = search_tag(category="mood")
                self.assertNotIn(obj1, result)
                self.assertIn(obj2, result)
                self.assertIn(obj3, result)
