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


import carlcsaposs.calculate_eth_taxes.currency as currency
import carlcsaposs.calculate_eth_taxes.exchange as exchange


def test_convert_acquire_transaction_to_acquired_eth():
    assert exchange.AcquireTransaction(
        datetime.datetime(2021, 3, 17), 500, 10340
    ).convert_to_acquired_eth() == currency.AcquiredETH(
        datetime.datetime(2021, 3, 17), 500, 10340
    )


def test_sort_transactions():
    transactions = [
        exchange.SpendTransaction(
            datetime.datetime(2021, 3, 17, 4, 2, 3),
            3583178900000000000,
            300000,
        ),
        exchange.AcquireTransaction(
            datetime.datetime(2021, 3, 17, 4, 2, 4),
            53583178900000000000,
            400000,
        ),
        exchange.SpendTransaction(
            datetime.datetime(2021, 3, 17, 4, 3, 1),
            3583178900000000000,
            300000,
        ),
    ]
    assert (
        exchange.sort_transactions_in_chronologial_order(
            [transactions[2], transactions[0], transactions[1]]
        )
        == transactions
    )
    assert (
        exchange.sort_transactions_in_chronologial_order(
            [transactions[0], transactions[1], transactions[2]]
        )
        == transactions
    )
    assert (
        exchange.sort_transactions_in_chronologial_order(
            [transactions[1], transactions[0], transactions[2]]
        )
        == transactions
    )


def test_sort_transactions_does_not_mutate_argument():
    unsorted_transactions = [
        exchange.SpendTransaction(
            datetime.datetime(2021, 3, 17, 4, 3, 1),
            3583178900000000000,
            300000,
        ),
        exchange.SpendTransaction(
            datetime.datetime(2021, 3, 17, 4, 2, 3),
            3583178900000000000,
            300000,
        ),
        exchange.AcquireTransaction(
            datetime.datetime(2021, 3, 17, 4, 2, 4),
            53583178900000000000,
            400000,
        ),
    ]
    assert unsorted_transactions != exchange.sort_transactions_in_chronologial_order(
        unsorted_transactions
    )


def test_convert_transactions_to_spent_eth_no_transactions():
    assert len(exchange.convert_transactions_to_spent_eth([], {})) == 0
