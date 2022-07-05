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
import datetime
import decimal
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


@pytest.mark.parametrize(
    ["time_acquired", "time_spent", "result"],
    [
        (
            datetime.datetime(1967, 2, 28, 23, 59, 59),
            datetime.datetime(1968, 2, 29),
            True,
        ),
        (
            datetime.datetime(2004, 2, 29),
            datetime.datetime(2005, 2, 28, 23, 59, 59),
            False,
        ),
        (
            datetime.datetime(3004, 2, 29),
            datetime.datetime(3005, 3, 1),
            True,
        ),
    ],
)
def test_is_long_term(time_acquired, time_spent, result):
    assert utils.is_long_term(time_acquired, time_spent) == result


@pytest.mark.parametrize(
    ["number", "places", "result"],
    [
        (decimal.Decimal("1.0050"), 2, decimal.Decimal("1.01")),
        (decimal.Decimal("1.0249"), 2, decimal.Decimal("1.02")),
        (decimal.Decimal("1.8"), 0, decimal.Decimal("2")),
        (decimal.Decimal("-3.254351"), 4, decimal.Decimal("-3.2544")),
    ],
)
def test_round_decimal(number: decimal.Decimal, places: int, result: decimal.Decimal):
    assert utils.round_decimal(number, places) == result


def test_round_decimal_invalid():
    with pytest.raises(ValueError):
        utils.round_decimal(decimal.Decimal("3.2"), -1)


def test_round_decimal_to_int():
    assert (
        utils.round_decimal_to_int(
            decimal.Decimal("2.4") + decimal.Decimal(".09999999999999999")
        )
        == 2
    )
