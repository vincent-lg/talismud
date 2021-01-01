# Copyright (c) 2020-20201, LE GOFF Vincent
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.

"""Module containing the ListView class.

A ListView can display a list of strings, in a horizontal or
vertical display.  Separators can also be specified.

"""

from enum import Enum, auto
from typing import Optional, Sequence

class ListViewOrientation(Enum):

    """Possible enumerations."""

    VERTICAL = auto()
    HORIZONTAL = auto()


class ListView:

    """
    A view for a list of strings.

    This will create a display somewhat to the `ls` command, where filenames are displayed in a vertical list with multiple columns, depending on the length of file names.

    """

    VERTICAL = ListViewOrientation.VERTICAL
    HORIZONTAL = ListViewOrientation.HORIZONTAL

    def __init__(self, min_col=15, max_width=80,
            orientation=ListViewOrientation.VERTICAL):
        self.min_col = min_col
        self.max_width = max_width
        self.orientation = orientation
        self.items = ItemOptions(self)
        self.sections = []

    def add_section(self, separator: str, items: Sequence[str]):
        """
        Add a new section.

        When displayed, the section title will aappear on its line, the
        items on following lines, depending on their number.

        Args:
            separator (str): the section's title, if any.
            itms (list of str): the items in this section.

        """
        self.sections.append((separator, sorted(items)))

    def render(self) -> str:
        """Render the list view, returning a formatted string."""
        # Determine the maximum lenth of all items
        bigger_item = max(len(item) for separator, section in self.sections
                for item in section)

        # Determine the number of columns
        min_col = self.min_col or 0
        col_width = max(min_col, bigger_item + 1)
        num_cols = (self.max_width - self.items.indent_width) // col_width

        # Create sections
        lines = []
        for separator, items in self.sections:
            if separator:
                lines.append(separator)

            # Display the lines of items
            num_lines = len(items) // num_cols
            if num_lines * num_cols < len(items):
                num_lines += 1

            line_items = []
            for num_line in range(num_lines):
                line_items.append([''] * num_cols)

            col = line = 0
            if self.orientation is ListViewOrientation.HORIZONTAL:
                # aa, ab, ac are placed on the same line
                for item in items:
                    line_items[line][col] = item
                    if col + 1 == num_cols:
                        line += 1
                        col = 0
                    else:
                        col += 1
            elif self.orientation is ListViewOrientation.VERTICAL:
                # aa, ab, ac are placed on the same column
                for item in items:
                    line_items[line][col] = item
                    if line + 1 == num_lines:
                        col += 1
                        line = 0
                    else:
                        line += 1
            else:
                raise ValueError("invalid orientation")

            # Display the result
            for line_item in line_items:
                line = self.items.indent_width * ' '
                for item in line_item:
                    line += str(item).ljust(col_width)

                lines.append(line.rstrip(' '))

        return "\n".join(lines)


class ItemOptions:

    """Options for items."""

    def __init__(self, view: ListView):
        self.indent_width = 0
