"""Condition in different tests."""

from test.scripting.abc import ScriptingTest

class TestCondition(ScriptingTest):

    """Test in conditions."""

    def test_only_if(self):
        """Test a if without an else block."""
        script = self.write_script("""
                variable = 5
                if variable == 5:
                    check = 30
                end
        """)
        check = script.get_variable_or_attribute("check")
        self.assertEqual(check, 30)

    def test_eq(self):
        """Test equality."""
        # Success
        script = self.write_script("""
                variable = 5
                if variable == 5:
                    check = 30
                else:
                    check = 20
                end
        """)
        check = script.get_variable_or_attribute("check")
        self.assertEqual(check, 30)

        # Failure
        script = self.write_script("""
                variable = 5
                if variable == 6:
                    check = 30
                else:
                    check = 20
                end
        """)
        check = script.get_variable_or_attribute("check")
        self.assertEqual(check, 20)

    def test_ne(self):
        """Test non-equality."""
        # Success
        script = self.write_script("""
                variable = 5
                if variable != 8:
                    check = 25
                else:
                    check = 15
                end
        """)
        check = script.get_variable_or_attribute("check")
        self.assertEqual(check, 25)

        # Failure
        script = self.write_script("""
                variable = 8
                if variable != 8:
                    check = 25
                else:
                    check = 15
                end
        """)
        check = script.get_variable_or_attribute("check")
        self.assertEqual(check, 15)

    def test_lt(self):
        """Test lower than."""
        # Success
        script = self.write_script("""
                variable = 5
                if variable < 10:
                    check = 50
                else:
                    check = 0
                end
        """)
        check = script.get_variable_or_attribute("check")
        self.assertEqual(check, 50)

        # Failure
        script = self.write_script("""
                variable = 5
                if variable < 2:
                    check = 50
                else:
                    check = 0
                end
        """)
        check = script.get_variable_or_attribute("check")
        self.assertEqual(check, 0)

    def test_le(self):
        """Test lower or equal to."""
        # Success
        script = self.write_script("""
                variable = 10
                if variable <= 10:
                    check = 80
                else:
                    check = 10
                end
        """)
        check = script.get_variable_or_attribute("check")
        self.assertEqual(check, 80)

        # Failure
        script = self.write_script("""
                variable = 10
                if variable <= 8:
                    check = 80
                else:
                    check = 10
                end
        """)
        check = script.get_variable_or_attribute("check")
        self.assertEqual(check, 10)

    def test_gt(self):
        """Test greater than."""
        # Success
        script = self.write_script("""
                variable = 5
                if variable > 2:
                    check = 90
                else:
                    check = -5
                end
        """)
        check = script.get_variable_or_attribute("check")
        self.assertEqual(check, 90)

        # Failure
        script = self.write_script("""
                variable = 5
                if variable > 10:
                    check = 90
                else:
                    check = -5
                end
        """)
        check = script.get_variable_or_attribute("check")
        self.assertEqual(check, -5)

    def test_ge(self):
        """Test greater or equal to."""
        # Success
        script = self.write_script("""
                variable = 5
                if variable >= 5:
                    check = 130
                else:
                    check = 0
                end
        """)
        check = script.get_variable_or_attribute("check")
        self.assertEqual(check, 130)

        # Failure
        script = self.write_script("""
                variable = 5
                if variable >= 8:
                    check = 130
                else:
                    check = 0
                end
        """)
        check = script.get_variable_or_attribute("check")
        self.assertEqual(check, 0)

    def test_combined(self):
        """Test an A < B < C condition."""
        # Success
        script = self.write_script("""
                variable = 5
                if 0 < variable < 10:
                    check = 150
                else:
                    check = 0
                end
        """)
        check = script.get_variable_or_attribute("check")
        self.assertEqual(check, 150)

        # Too low
        script = self.write_script("""
                variable = -2
                if 0 < variable < 10:
                    check = 150
                else:
                    check = 0
                end
        """)
        check = script.get_variable_or_attribute("check")
        self.assertEqual(check, 0)

        # Too high
        script = self.write_script("""
                variable = 12
                if 0 < variable < 10:
                    check = 150
                else:
                    check = 0
                end
        """)
        check = script.get_variable_or_attribute("check")
        self.assertEqual(check, 0)
