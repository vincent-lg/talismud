"""Object representation in different tests."""

from data.character import Character
from test.scripting.abc import ScriptingTest

class TestRepresentation(ScriptingTest):

    """Test in object representations."""

    def test_character(self):
        character = self.create_character()
        script = self.write_script("""
                character2 = character
                character2.msg("Something is working for {character}")
        """, variables={"character": character})

