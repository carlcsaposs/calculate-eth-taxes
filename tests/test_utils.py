"""
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
# pylint: disable=missing-docstring
import pytest

import carlcsaposs.calculate_eth_taxes.utils as utils


def test_number_domain_validate_number():
    with pytest.raises(ValueError) as exception_info:
        utils.NumberDomain.POSITIVE.validate_number("key", 0)
    assert (
        str(exception_info.value) == "expected 'key' greater than zero, got 0 instead"
    )
    assert utils.NumberDomain.POSITIVE.validate_number("key", 1) is None
    with pytest.raises(ValueError) as exception_info:
        utils.NumberDomain.NON_NEGATIVE.validate_number("key", -2)
    assert (
        str(exception_info.value)
        == "expected 'key' greater than or equal to zero, got -2 instead"
    )
    assert utils.NumberDomain.NON_NEGATIVE.validate_number("key", 0) is None
