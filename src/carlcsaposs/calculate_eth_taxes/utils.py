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
import datetime
import enum


class NumberDomain(enum.Enum):
    """Valid domain for an integer"""

    POSITIVE = (lambda x: x > 0, "greater than zero")
    NON_NEGATIVE = (lambda x: x >= 0, "greater than or equal to zero")

    def validate_number(self, key: str, number: int) -> None:
        """Raise ValueError if number is not within domain"""
        if not self.value[0](number):
            raise ValueError(f"expected '{key}' {self.value[1]}, got {number} instead")


def is_long_term(
    time_acquired: datetime.datetime, time_spent: datetime.datetime
) -> bool:
    """Long term is one calendar year or more*

    *Does not include date of acquistion
    """
    # Including date of acquistion, long term is more than one calendar
    # year.
    acquired: datetime.date = time_acquired.date()
    spent: datetime.date = time_spent.date()
    try:
        acquired = acquired.replace(year=acquired.year + 1)
    except ValueError:
        if acquired.day == 29 and acquired.month == 2:
            # Leap day
            acquired = acquired.replace(year=acquired.year + 1, day=28)
        else:
            raise
    return acquired < spent
