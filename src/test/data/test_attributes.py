"""Test the behavir of object with attributes."""

from data.base import db
from test.base import BaseTest

SUPPORTED = (db.Character, db.Room)

class TestAttributes(BaseTest):

    def test_add(self):
        """Add attributes to the objects suppoorting it."""
        for supported in SUPPORTED:
            cls_name = supported.__name__
            with self.subTest(msg=f"in class {cls_name}"):
                tested = self.create_instance(supported)
                self.assertEqual(len(tested.db), 0)

                # The 'thinige' attribute shouldn't exist
                self.assertFalse('thingie' in tested.db)
                with self.assertRaises(ValueError):
                    thingie = tested.db.thingie

                # Create the 'thingie' attribute in this instance
                tested.db.thingie = 3

                # Check that the returned value is accurate (expect 3)
                self.assertEqual(tested.db.thingie, 3)

                # Check that `thingie` is in the attributes
                self.assertTrue(any(attr for attr in tested.db
                        if attr.name == 'thingie'))
                self.assertTrue('thingie' in tested.db)

                # Add a second attribute, 'attempt', of value 4
                # The 'attempt' attribute shouldn't exist
                self.assertFalse('attempt' in tested.db)
                with self.assertRaises(ValueError):
                    attempt = tested.db.atempt

                # Create the 'attempt' attribute in this instance
                tested.db.attempt = 4

                # Check that the returned value is accurate (expect 4)
                self.assertEqual(tested.db.attempt, 4)

                # Check that `attempt` is in the attributes
                self.assertTrue(any(attr for attr in tested.db
                        if attr.name == 'attempt'))
                self.assertTrue('attempt' in tested.db)

                # Check that the 'thingie' attribute still exists
                self.assertEqual(tested.db.thingie, 3)

                # Check that there are two stored attributes at this point
                self.assertEqual(len(tested.db), 2)

                # Create a third attribute, 'friend', with a value of
                # another character.  This is useful to make sure
                # object identity is correctly preserved.
                friend = self.create_character()
                tested.db.friend = friend
                self.assertIs(tested.db.friend, friend)

    def test_update(self):
        """Test to update attributes."""
        for supported in SUPPORTED:
            cls_name = supported.__name__
            with self.subTest(msg=f"in class {cls_name}"):
                tested = self.create_instance(supported)
                self.assertEqual(len(tested.db), 0)

                # Create the 'name' attribute in this instance
                tested.db.name = "Susan"

                # Check that the returned value is accurate (expect 'Susan')
                self.assertEqual(tested.db.name, 'Susan')

                # Update the 'name' attribute to 'Henri'
                tested.db.name = "Henri"

                # Check that the returned value is accurate (expect 'Henri')
                self.assertEqual(tested.db.name, 'Henri')

                # Make sure there is only one attribute 'name'
                self.assertEqual(len(tested.db), 1)

    def test_delete(self):
        """Try to delete attributes in supported objects."""
        for supported in SUPPORTED:
            cls_name = supported.__name__
            with self.subTest(msg=f"in class {cls_name}"):
                tested = self.create_instance(supported)
                self.assertEqual(len(tested.db), 0)

                # Create the 'tmp' attribute in this instance
                tested.db.tmp = 100

                # Check that the returned value is accurate (expect 100)
                self.assertEqual(tested.db.tmp, 100)

                # Try to delete this attribute
                del tested.db.tmp

                # There should be no attribute
                self.assertEqual(len(tested.db), 0)

                # And accessing the attribute should raise an exception
                with self.assertRaises(ValueError):
                    tmp = tested.db.tmp

                # Recreate it with a different valye, then create a second
                # attribute and delete the first one.
                tested.db.tmp = 200

                # Check that the returned value is accurate (expect 200)
                self.assertEqual(tested.db.tmp, 200)

                # Create the 'tmp2' attribute
                tested.db.tmp2 = 300

                # Check that the returned value is accurate (expect 300)
                self.assertEqual(tested.db.tmp2, 300)

                # Delete 'tmp'
                del tested.db.tmp

                # There should be one attribute left
                self.assertEqual(len(tested.db), 1)

                # And accessing the 'tmp' attribute should raise an exception
                with self.assertRaises(ValueError):
                    tmp = tested.db.tmp

                # But accessing 'tmp2' should still work as expected
                self.assertEqual(tested.db.tmp2, 300)
