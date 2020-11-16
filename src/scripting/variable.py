import inspect
from string import Formatter

UNKNOWN = object()

class VariableFormatter(Formatter):

    """Formatter specifically designed for variables in messages."""

    def __init__(self, character, variables=None):
        self.character = character
        self.variables = variables
        if variables is None:
            self.variables = {}
            frame = inspect.currentframe().f_back
            while frame and (locals := frame.f_locals):
                self.variables.update(dict(locals))
                frame = frame.f_back

    def get_field(self, field_name, args, kwargs):
        """
        Retrieve the field name.

        The field name might be found in the local variables of
        the previous frames.

        """
        full_name = field_name
        names = field_name.split(".")
        field_name = names[0]
        if field_name.isdigit() or field_name in kwargs:
            return super().get_field(full_name, args, kwargs)

        value = self.variables.get(field_name, UNKNOWN)
        if value is not UNKNOWN:
            for name in names[1:]:
                value = getattr(value, name)

            return (value, full_name)

        raise ValueError(f"cannot find the variable name: {field_name!r}")

    def format_field(self, value, format_spec):
        """
        Add support for simple pluralization.

        The syntax can be used on integer formatters like this:

            >>> num = 1
            >>> "I see {num} {num:dog/dogs}"
            'I see 1 dog'
            >>> num = 2
            >>> "I see {num} {num:dog/dogs}"
            'I see 2 dogs'

        The syntax is as follows: first the identifier
        between braces which should refer to an integer, then a
        colon (:), then the singular name, a slash (/) and
        the plural name.  The singular name will be selected
        if the number is 1, otherwise, the plural name will
        be selected.

        In the previous example, the number to format, called `num`,
        is in a variable defined before calling the formatter.  The
        formatter will look for the variable value and will choose
        which word to display based on this value.  Here are more examples:

            >>> num_dogs = 1
            >>> "There {num_dogs:is/are} {num_dogs} {num_dogs:dog/dogs} here!"
            'There is 1 dog here!'
            >>> apples = 4
            >>> oranges = 1
            >>> "I have {oranges} {oranges:orange/oranges} and " \
            ...     "{apples} {apples:apple/apples}."
            'I have 1 orange and 4 apples.'

        """
        if len(format_spec) > 1 and "/" in format_spec[1:]:
            singular, plural = format_spec.split('/')
            if value == 1:
                return singular
            else:
                return plural
        else:
            return super().format_field(value, format_spec)
