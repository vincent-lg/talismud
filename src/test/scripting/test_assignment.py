"""Assigning values in different tests."""

from test.scripting.abc import ScriptingTest

class TestAssignment(ScriptingTest):

    """Test to assign values."""

    def test_int(self):
        """Create a variable with a simple integer value."""
        script = self.write_script("variable = 5")
        variable = script.get_variable_or_attribute("variable")
        self.assertEqual(variable, 5)

    def test_float(self):
        """Create a variable with a simple float value."""
        script = self.write_script("variable = 2.5")
        variable = script.get_variable_or_attribute("variable")
        self.assertEqual(variable, 2.5)

    def test_var(self):
        """Create a copy variable."""
        script = self.write_script("""
                variable1 = 12
                variable2 = variable1
        """)
        variable2 = script.get_variable_or_attribute("variable2")
        self.assertEqual(variable2, 12)

    def test_str_apostrophes(self):
        """Create a variable with a simple string surrounded by apostrophes."""
        script = self.write_script("variable = 'ok'")
        variable = script.get_variable_or_attribute("variable")
        self.assertEqual(variable, "ok")

    def test_str_double_quotes(self):
        """Create a variable with a string surrounded by double quotes."""
        script = self.write_script("variable = \"thanks\"")
        variable = script.get_variable_or_attribute("variable")
        self.assertEqual(variable, "thanks")

    def test_str_mul_ded(self):
        """Create a variable with a multiline string using ""> <""."""
        script = self.write_script("""
                variable = "">
                        This is a string
                        with at least
                        three lines.
                <""
        """)
        variable = script.get_variable_or_attribute("variable")
        self.assertEqual(variable,
                "This is a string with at least three lines.")

    def test_str_mul_pre(self):
        """Create a variable with a multiline string using ""| |""."""
        script = self.write_script("""
                variable = ""|
                        This is a string
                        with at least
                        three lines.
                |""
        """)
        variable = script.get_variable_or_attribute("variable")
        self.assertEqual(variable,
                "This is a string\nwith at least\nthree lines.")

    def test_negative_int(self):
        """Create a variable with a simple integer value."""
        script = self.write_script("variable = -5")
        variable = script.get_variable_or_attribute("variable")
        self.assertEqual(variable, -5)

    def test_negative_float(self):
        """Create a variable with a simple float value."""
        script = self.write_script("variable = -2.5")
        variable = script.get_variable_or_attribute("variable")
        self.assertEqual(variable, -2.5)

    def test_negative_var(self):
        """Create a copy variable, the second is negative."""
        script = self.write_script("""
                variable1 = 12
                variable2 = -variable1
        """)
        variable2 = script.get_variable_or_attribute("variable2")
        self.assertEqual(variable2, -12)

    def test_add(self):
        """Affect a variable to an addition."""
        script = self.write_script("variable = 2 + 8")
        variable = script.get_variable_or_attribute("variable")
        self.assertEqual(variable, 10)

    def test_sub(self):
        """Affect a variable to a subtraction."""
        script = self.write_script("variable = 2 - 8")
        variable = script.get_variable_or_attribute("variable")
        self.assertEqual(variable, -6)

    def test_mul(self):
        """Affect a variable to a multiplication."""
        script = self.write_script("variable = 2 * 8")
        variable = script.get_variable_or_attribute("variable")
        self.assertEqual(variable, 16)

    def test_div(self):
        """Affect a variable to a division."""
        script = self.write_script("variable = 2 / 8")
        variable = script.get_variable_or_attribute("variable")
        self.assertEqual(variable, 0.25)
