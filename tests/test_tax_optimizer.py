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

import carlcsaposs.calculate_eth_taxes.currency as currency
import carlcsaposs.calculate_eth_taxes.exchange_transactions as exchange_transactions
import carlcsaposs.calculate_eth_taxes.tax_optimizer as tax_optimizer


@pytest.mark.parametrize(
    ["acquired_eths", "sorted_acquired_eths"],
    [
        ([], []),
        (
            [
                currency.AcquiredETH(
                    datetime.datetime(2022, 3, 13, 20, 10, 59),
                    3583178900000000000,
                    257075,
                )
            ],
            [
                currency.AcquiredETH(
                    datetime.datetime(2022, 3, 13, 20, 10, 59),
                    3583178900000000000,
                    257075,
                )
            ],
        ),
        (
            [
                currency.AcquiredETH(
                    datetime.datetime(2022, 3, 13, 20, 10, 59),
                    3583178900000000000,
                    257075,
                ),
                currency.AcquiredETH(
                    datetime.datetime(2022, 3, 13, 20, 11),
                    2168500000000000,
                    257074,
                ),
            ],
            [
                currency.AcquiredETH(
                    datetime.datetime(2022, 3, 13, 20, 11),
                    2168500000000000,
                    257074,
                ),
                currency.AcquiredETH(
                    datetime.datetime(2022, 3, 13, 20, 10, 59),
                    3583178900000000000,
                    257075,
                ),
            ],
        ),
        (
            [
                currency.AcquiredETH(
                    datetime.datetime(2025, 3, 13, 20, 10, 59),
                    3583178900000000000,
                    257075,
                ),
                currency.AcquiredETH(
                    datetime.datetime(2022, 3, 13, 20, 11),
                    2168500000000000,
                    257074,
                ),
            ],
            [
                currency.AcquiredETH(
                    datetime.datetime(2025, 3, 13, 20, 10, 59),
                    3583178900000000000,
                    257075,
                ),
                currency.AcquiredETH(
                    datetime.datetime(2022, 3, 13, 20, 11),
                    2168500000000000,
                    257074,
                ),
            ],
        ),
    ],
)
def test_first_in_first_out(
    acquired_eths: list[currency.AcquiredETH],
    sorted_acquired_eths: list[currency.AcquiredETH],
):
    assert (
        tax_optimizer.FirstInFirstOut.sort(acquired_eths, None) == sorted_acquired_eths
    )


@pytest.mark.parametrize(
    ["acquired_eths", "transaction", "sorted_acquired_eths"],
    [
        (
            [],
            exchange_transactions.Spend(
                datetime.datetime(2022, 3, 13), 0, decimal.Decimal("0")
            ),
            [],
        ),
        (
            [
                currency.AcquiredETH(
                    datetime.datetime(2022, 3, 13),
                    3583178900000000000,
                    decimal.Decimal("257075"),
                )
            ],
            exchange_transactions.Spend(
                datetime.datetime(2022, 3, 13), 0, decimal.Decimal("0")
            ),
            [
                currency.AcquiredETH(
                    datetime.datetime(2022, 3, 13),
                    3583178900000000000,
                    decimal.Decimal("257075"),
                )
            ],
        ),
        (
            [
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 14),
                    78900000000000,
                    decimal.Decimal("57076"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 13),
                    78900000000000,
                    decimal.Decimal("57075"),
                ),
            ],
            exchange_transactions.Spend(
                datetime.datetime(2022, 3, 13), 0, decimal.Decimal("57075")
            ),
            [
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 13),
                    78900000000000,
                    decimal.Decimal("57075"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 14),
                    78900000000000,
                    decimal.Decimal("57076"),
                ),
            ],
        ),
        (
            [
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 14),
                    78900000000000,
                    decimal.Decimal("57076"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 13),
                    78900000000000,
                    decimal.Decimal("57075"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 12),
                    78900000000000,
                    decimal.Decimal("57075"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 10),
                    78900000000000,
                    decimal.Decimal("57070"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 11),
                    78900000000000,
                    decimal.Decimal("657075"),
                ),
            ],
            exchange_transactions.Spend(
                datetime.datetime(2022, 3, 13), 0, decimal.Decimal("57075")
            ),
            [
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 11),
                    78900000000000,
                    decimal.Decimal("657075"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 12),
                    78900000000000,
                    decimal.Decimal("57075"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 10),
                    78900000000000,
                    decimal.Decimal("57070"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 13),
                    78900000000000,
                    decimal.Decimal("57075"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 14),
                    78900000000000,
                    decimal.Decimal("57076"),
                ),
            ],
        ),
        (
            [
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 15),
                    78900000000000,
                    decimal.Decimal("57076"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 13),
                    78900000000000,
                    decimal.Decimal("57075"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 12),
                    78900000000000,
                    decimal.Decimal("57075"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 14),
                    78900000000000,
                    decimal.Decimal("57074"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 10),
                    78900000000000,
                    decimal.Decimal("57070"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 16),
                    78900000000000,
                    decimal.Decimal("1"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 11),
                    78900000000000,
                    decimal.Decimal("657075"),
                ),
            ],
            exchange_transactions.Spend(
                datetime.datetime(2022, 3, 13), 0, decimal.Decimal("57075")
            ),
            [
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 14),
                    78900000000000,
                    decimal.Decimal("57074"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 16),
                    78900000000000,
                    decimal.Decimal("1"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 11),
                    78900000000000,
                    decimal.Decimal("657075"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 12),
                    78900000000000,
                    decimal.Decimal("57075"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 10),
                    78900000000000,
                    decimal.Decimal("57070"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 13),
                    78900000000000,
                    decimal.Decimal("57075"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 15),
                    78900000000000,
                    decimal.Decimal("57076"),
                ),
            ],
        ),
    ],
)
def test_lower_tax_bracket(
    acquired_eths: list[currency.AcquiredETH],
    transaction: exchange_transactions.Spend,
    sorted_acquired_eths: list[currency.AcquiredETH],
):
    assert (
        tax_optimizer.LowerTaxBracket.sort(acquired_eths, transaction)
        == sorted_acquired_eths
    )


@pytest.mark.parametrize(
    ["acquired_eths", "transaction", "sorted_acquired_eths"],
    [
        (
            [
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 14),
                    78900000000000,
                    decimal.Decimal("57076"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 13),
                    78900000000000,
                    decimal.Decimal("57075"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 12),
                    78900000000000,
                    decimal.Decimal("57075"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 10),
                    78900000000000,
                    decimal.Decimal("57070"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 11),
                    78900000000000,
                    decimal.Decimal("657075"),
                ),
            ],
            exchange_transactions.Spend(
                datetime.datetime(2022, 3, 13), 0, decimal.Decimal("57075")
            ),
            [
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 10),
                    78900000000000,
                    decimal.Decimal("57070"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 12),
                    78900000000000,
                    decimal.Decimal("57075"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 11),
                    78900000000000,
                    decimal.Decimal("657075"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 13),
                    78900000000000,
                    decimal.Decimal("57075"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 14),
                    78900000000000,
                    decimal.Decimal("57076"),
                ),
            ],
        ),
        (
            [
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 15),
                    78900000000000,
                    decimal.Decimal("57076"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 13),
                    78900000000000,
                    decimal.Decimal("57075"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 12),
                    78900000000000,
                    decimal.Decimal("57075"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 14),
                    78900000000000,
                    decimal.Decimal("57074"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 10),
                    78900000000000,
                    decimal.Decimal("57070"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 16),
                    78900000000000,
                    decimal.Decimal("1"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 11),
                    78900000000000,
                    decimal.Decimal("657075"),
                ),
            ],
            exchange_transactions.Spend(
                datetime.datetime(2022, 3, 13), 0, decimal.Decimal("57075")
            ),
            [
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 14),
                    78900000000000,
                    decimal.Decimal("57074"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 16),
                    78900000000000,
                    decimal.Decimal("1"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 10),
                    78900000000000,
                    decimal.Decimal("57070"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 12),
                    78900000000000,
                    decimal.Decimal("57075"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 11),
                    78900000000000,
                    decimal.Decimal("657075"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 13),
                    78900000000000,
                    decimal.Decimal("57075"),
                ),
                currency.AcquiredETH(
                    datetime.datetime(2021, 3, 15),
                    78900000000000,
                    decimal.Decimal("57076"),
                ),
            ],
        ),
    ],
)
def test_higher_tax_bracket(
    acquired_eths: list[currency.AcquiredETH],
    transaction: exchange_transactions.Spend,
    sorted_acquired_eths: list[currency.AcquiredETH],
):
    assert (
        tax_optimizer.HigherTaxBracket.sort(acquired_eths, transaction)
        == sorted_acquired_eths
    )
