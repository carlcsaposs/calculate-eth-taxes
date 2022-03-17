"""
utils: Miscellaneous utilities used by multiple other modules

Copyright (C) 2022 Carl Csaposs

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import enum


class NumberDomain(enum.Enum):
    """Valid domain for an integer"""

    POSITIVE = (lambda x: x > 0, "greater than zero")
    NON_NEGATIVE = (lambda x: x >= 0, "greater than or equal to zero")

    def validate_number(self, key: str, number: int):
        """Raise ValueError if number is not within domain"""
        if not self.value[0](number):
            raise ValueError(f"expected '{key}' {self.value[1]}, got {number} instead")
