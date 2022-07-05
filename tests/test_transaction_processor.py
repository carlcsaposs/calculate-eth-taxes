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

import carlcsaposs.calculate_eth_taxes.currency as currency
import carlcsaposs.calculate_eth_taxes.exchange_transactions as exchange_transactions
import carlcsaposs.calculate_eth_taxes.tax_optimizer as tax_optimizer
import carlcsaposs.calculate_eth_taxes.transaction_processor as transaction_processor


def test_sort_transactions():
    transactions = [
        exchange_transactions.Spend(
            datetime.datetime(2021, 3, 17, 4, 2, 3),
            3583178900000000000,
            300000,
        ),
        exchange_transactions.Acquire(
            datetime.datetime(2021, 3, 17, 4, 2, 4),
            53583178900000000000,
            400000,
        ),
        exchange_transactions.Spend(
            datetime.datetime(2021, 3, 17, 4, 3, 1),
            3583178900000000000,
            300000,
        ),
    ]
    processor = transaction_processor._TransactionProcessor(
        [transactions[2], transactions[0], transactions[1]],
        {2021: tax_optimizer.FirstInFirstOut},
    )
    processor.sort_transactions_in_chronologial_order()
    assert processor.transactions == transactions

    processor = transaction_processor._TransactionProcessor(
        [transactions[0], transactions[1], transactions[2]],
        {2021: tax_optimizer.FirstInFirstOut},
    )
    processor.sort_transactions_in_chronologial_order()
    assert processor.transactions == transactions

    processor = transaction_processor._TransactionProcessor(
        [transactions[1], transactions[0], transactions[2]],
        {2021: tax_optimizer.FirstInFirstOut},
    )
    processor.sort_transactions_in_chronologial_order()
    assert processor.transactions == transactions


def test_convert_transactions_to_spent_eth_no_transactions():
    assert len(transaction_processor.convert_transactions_to_spent_eth([], {})) == 0


def test_convert_transactions_first_in_first_out_one_output():
    transactions = [
        exchange_transactions.Acquire(
            datetime.datetime(2022, 3, 17, 16, 21, 3),
            3,
            280900,
        ),
        exchange_transactions.Spend(
            datetime.datetime(2022, 3, 17, 16, 21, 4),
            2,
            280688,
        ),
    ]
    assert transaction_processor.convert_transactions_to_spent_eth(
        transactions, {2022: tax_optimizer.FirstInFirstOut}
    ) == [
        currency.SpentETH(
            datetime.datetime(2022, 3, 17, 16, 21, 3),
            datetime.datetime(2022, 3, 17, 16, 21, 4),
            2,
            ((280900 * 2) / decimal.Decimal(100 * 10**18)).to_integral_value(
                rounding=decimal.ROUND_HALF_UP
            ),
            ((280688 * 2) / decimal.Decimal(100 * 10**18)).to_integral_value(
                rounding=decimal.ROUND_HALF_UP
            ),
        )
    ]


def test_convert_transactions_first_in_first_out_multiple_outputs():
    transactions = [
        # not in chronological order
        exchange_transactions.Spend(
            datetime.datetime(2022, 4, 17, 16, 21, 4),
            200000000000000000,
            4028,
        ),
        exchange_transactions.Acquire(
            datetime.datetime(2022, 3, 17, 16, 21, 3),
            400000000000000000,
            280900,
        ),
        exchange_transactions.Spend(
            datetime.datetime(2022, 3, 17, 16, 21, 4),
            300000000000000000,
            280688,
        ),
        exchange_transactions.Acquire(
            datetime.datetime(2021, 3, 17, 16, 21, 3),
            100000000000000000,
            280900,
        ),
    ]
    assert transaction_processor.convert_transactions_to_spent_eth(
        transactions, {2022: tax_optimizer.FirstInFirstOut}
    ) == [
        currency.SpentETH(
            datetime.datetime(2021, 3, 17, 16, 21, 3),
            datetime.datetime(2022, 3, 17, 16, 21, 4),
            100000000000000000,
            (
                (280900 * 100000000000000000) / decimal.Decimal(100 * 10**18)
            ).to_integral_value(rounding=decimal.ROUND_HALF_UP),
            (
                (280688 * 100000000000000000) / decimal.Decimal(100 * 10**18)
            ).to_integral_value(rounding=decimal.ROUND_HALF_UP),
        ),
        currency.SpentETH(
            datetime.datetime(2022, 3, 17, 16, 21, 3),
            datetime.datetime(2022, 3, 17, 16, 21, 4),
            200000000000000000,
            (
                (280900 * 200000000000000000) / decimal.Decimal(100 * 10**18)
            ).to_integral_value(rounding=decimal.ROUND_HALF_UP),
            (
                (280688 * 200000000000000000) / decimal.Decimal(100 * 10**18)
            ).to_integral_value(rounding=decimal.ROUND_HALF_UP),
        ),
        currency.SpentETH(
            datetime.datetime(2022, 3, 17, 16, 21, 3),
            datetime.datetime(2022, 4, 17, 16, 21, 4),
            200000000000000000,
            (
                (280900 * 200000000000000000) / decimal.Decimal(100 * 10**18)
            ).to_integral_value(rounding=decimal.ROUND_HALF_UP),
            (
                (4028 * 200000000000000000) / decimal.Decimal(100 * 10**18)
            ).to_integral_value(rounding=decimal.ROUND_HALF_UP),
        ),
    ]
