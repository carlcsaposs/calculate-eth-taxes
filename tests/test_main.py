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

import pytest

import carlcsaposs.calculate_eth_taxes.file_writer as file_writer
import carlcsaposs.calculate_eth_taxes.main as main


@pytest.mark.parametrize(
    ["override_key", "override_value"],
    [("cost_usd_including_fees", -3), ("proceeds_usd_excluding_fees", -1)],
)
def test_spent_eth_negative(override_key: str, override_value: int):
    row_dict = {
        "time_acquired": datetime.datetime(1940, 4, 3),
        "time_spent": datetime.datetime(1941, 9, 29),
        "amount_wei": 300000000000000000,
        "cost_usd_including_fees": 0,
        "proceeds_usd_excluding_fees": 0,
    }
    row_dict[override_key] = override_value
    with pytest.raises(ValueError) as exception_info:
        main.SpentETH(**row_dict)
    assert (
        str(exception_info.value)
        == f"expected '{override_key}' greater than or equal to zero, got {override_value} instead"
    )


def test_spent_eth_zero_amount():
    with pytest.raises(ValueError) as exception_info:
        main.SpentETH(
            datetime.datetime(1940, 4, 3), datetime.datetime(1941, 9, 29), 0, 5, 3
        )
    assert (
        str(exception_info.value)
        == "expected 'amount_wei' greater than zero, got 0 instead"
    )


def test_spent_eth_spent_before_acquired():
    with pytest.raises(ValueError) as exception_info:
        main.SpentETH(
            datetime.datetime(1940, 4, 3, 1, 1, 1),
            datetime.datetime(1940, 4, 3, 1, 1, 1),
            200000000000000000,
            5,
            3,
        )
    assert str(exception_info.value) == "'time_spent' must be after 'time_acquired'"


@pytest.mark.parametrize(
    ["spent_eth", "form_row"],
    [
        (
            main.SpentETH(
                datetime.datetime(1967, 2, 28, 23, 59, 59),
                datetime.datetime(1968, 2, 29),
                400000000000000,
                1,
                0,
            ),
            file_writer.Form8949Row(
                1968, True, "0.000400000000000000 ETH", "02/28/1967", "02/29/1968", 0, 1
            ),
        ),
        (
            main.SpentETH(
                datetime.datetime(2004, 2, 29),
                datetime.datetime(2005, 2, 28, 23, 59, 59),
                34000000000000000000,
                5000,
                4930,
            ),
            file_writer.Form8949Row(
                2005,
                False,
                "34.000000000000000000 ETH",
                "02/29/2004",
                "02/28/2005",
                4930,
                5000,
            ),
        ),
        (
            main.SpentETH(
                datetime.datetime(3004, 2, 29),
                datetime.datetime(3005, 3, 1),
                100000000000000000,
                1,
                0,
            ),
            file_writer.Form8949Row(
                3005, True, "0.100000000000000000 ETH", "02/29/3004", "03/01/3005", 0, 1
            ),
        ),
    ],
)
def test_convert_spent_eth_to_form_8949_row(
    spent_eth: main.SpentETH, form_row: file_writer.Form8949Row
):
    assert spent_eth.convert_to_form_8949_row() == form_row


@pytest.mark.parametrize(
    ["override_key", "override_value"],
    [("amount_wei", 0), ("cost_us_cents_per_eth_including_fees", 0)],
)
def test_acquired_eth_non_positive(override_key: str, override_value: int):
    row_dict = {
        "time_acquired": datetime.datetime(1940, 4, 3),
        "amount_wei": 1,
        "cost_us_cents_per_eth_including_fees": 120000,
    }
    row_dict[override_key] = override_value
    with pytest.raises(ValueError) as exception_info:
        main.AcquiredETH(**row_dict)
    assert (
        str(exception_info.value)
        == f"expected '{override_key}' greater than zero, got {override_value} instead"
    )


def test_convert_acquired_eth_to_spent_eth():
    acquired_eth = main.AcquiredETH(
        datetime.datetime(2022, 3, 13, 20, 10, 59), 3583178900000000000, 257075
    )
    time_spent = datetime.datetime(2022, 3, 13, 20, 11, 2)
    spent_eth = main.SpentETH(
        datetime.datetime(2022, 3, 13, 20, 10, 59),
        time_spent,
        3583178900000000000,
        int(3.5831789 * 2570.75),
        int(3.5831789 * 2568.32),
    )
    assert acquired_eth.convert_to_spent_eth(time_spent, 256832) == spent_eth


def test_acquired_eth_remove():
    original_instance = main.AcquiredETH(
        datetime.datetime(1970, 1, 1), 48290000000000, 392342141232423
    )
    new_instance = main.AcquiredETH(
        datetime.datetime(1970, 1, 1),
        2390000000000,
        392342141232423,
    )
    assert original_instance.remove_wei(2390000000000) == new_instance
    assert original_instance.amount_wei == 48290000000000 - 2390000000000


@pytest.mark.parametrize("amount", [0, 5030000000000000001])
def test_acquired_eth_remove_invalid_amount(amount: int):
    acquired_eth = main.AcquiredETH(
        datetime.datetime(2034, 11, 29), 5030000000000000000, 1230
    )
    with pytest.raises(ValueError) as exception_info:
        acquired_eth.remove_wei(amount)
    assert (
        str(exception_info.value)
        == f"expected value between 0 and 5030000000000000000, got {amount} instead"
    )


def test_convert_acquire_transaction_to_acquired_eth():
    assert main.AcquireTransaction(
        datetime.datetime(2021, 3, 17), 500, 10340
    ).convert_to_acquired_eth() == main.AcquiredETH(
        datetime.datetime(2021, 3, 17), 500, 10340
    )


def test_sort_transactions():
    transactions = [
        main.SpendTransaction(
            datetime.datetime(2021, 3, 17, 4, 2, 3),
            3583178900000000000,
            300000,
        ),
        main.AcquireTransaction(
            datetime.datetime(2021, 3, 17, 4, 2, 4),
            53583178900000000000,
            400000,
        ),
        main.SpendTransaction(
            datetime.datetime(2021, 3, 17, 4, 3, 1),
            3583178900000000000,
            300000,
        ),
    ]
    assert (
        main.sort_transactions_in_chronologial_order(
            [transactions[2], transactions[0], transactions[1]]
        )
        == transactions
    )
    assert (
        main.sort_transactions_in_chronologial_order(
            [transactions[0], transactions[1], transactions[2]]
        )
        == transactions
    )
    assert (
        main.sort_transactions_in_chronologial_order(
            [transactions[1], transactions[0], transactions[2]]
        )
        == transactions
    )


def test_sort_transactions_does_not_mutate_argument():
    unsorted_transactions = [
        main.SpendTransaction(
            datetime.datetime(2021, 3, 17, 4, 3, 1),
            3583178900000000000,
            300000,
        ),
        main.SpendTransaction(
            datetime.datetime(2021, 3, 17, 4, 2, 3),
            3583178900000000000,
            300000,
        ),
        main.AcquireTransaction(
            datetime.datetime(2021, 3, 17, 4, 2, 4),
            53583178900000000000,
            400000,
        ),
    ]
    assert unsorted_transactions != main.sort_transactions_in_chronologial_order(
        unsorted_transactions
    )
