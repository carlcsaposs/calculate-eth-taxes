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

import carlcsaposs.calculate_eth_taxes.exchange_transactions as exchange_transactions
import carlcsaposs.calculate_eth_taxes.file_reader as file_reader


def test_convert_fee_to_spend_transaction():
    wallet_transaction = file_reader.WalletTransaction(
        datetime.datetime(2022, 7, 5),
        "0x061f7937b7b2bc7596539959804f86538b6368dc",
        "0x8fa9b96f3d08165f26256931b39d973a237b29f3",
        23425000000,
        5000000,
        decimal.Decimal("10258"),
    )
    assert (
        wallet_transaction.convert_fee_to_spend_transaction()
        == exchange_transactions.Spend(
            datetime.datetime(2022, 7, 5), 5000000, decimal.Decimal("0")
        )
    )


def test_convert_amount_to_spend_transaction():
    wallet_transaction = file_reader.WalletTransaction(
        datetime.datetime(2022, 7, 5),
        "0x061f7937b7b2bc7596539959804f86538b6368dc",
        "0x8fa9b96f3d08165f26256931b39d973a237b29f3",
        23425000000,
        5000000,
        decimal.Decimal("10258"),
    )
    assert (
        wallet_transaction.convert_amount_to_spend_transaction()
        == exchange_transactions.Spend(
            datetime.datetime(2022, 7, 5), 23425000000, decimal.Decimal("10258")
        )
    )


def test_convert_coinbase_timestamp_to_datetime():
    assert file_reader.convert_coinbase_timestamp_to_datetime(
        "2022-07-05T23:16:51Z"
    ) == datetime.datetime(2022, 7, 5, 23, 16, 51)


def test_convert_coinbase_pro_timestamp_to_datetime():
    assert file_reader.convert_coinbase_pro_timestamp_to_datetime(
        "2022-07-05T23:16:51.802Z"
    ) == datetime.datetime(2022, 7, 5, 23, 16, 51, 802000)
