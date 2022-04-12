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
import carlcsaposs.calculate_eth_taxes.exchange_transactions as exchange_transactions


def test_convert_acquire_transaction_to_acquired_eth():
    assert exchange_transactions.Acquire(
        datetime.datetime(2021, 3, 17), 500, 10340
    ).convert_to_acquired_eth() == currency.AcquiredETH(
        datetime.datetime(2021, 3, 17), 500, 10340
    )
