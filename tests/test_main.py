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
import collections
import csv
import dataclasses
import datetime
import pathlib
import typing
import pytest
import carlcsaposs.calculate_eth_taxes.main as main


def test_write_form_8949_zero_rows(tmp_path: pathlib.Path):
    file_path = tmp_path / "form-8949.csv"
    main.Form8949File([]).write_to_file(file_path)
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        assert reader.fieldnames == main.Form8949File.FIELDNAMES
        # Check for zero rows
        assert next(reader, False) is False


def cast_string(value: str, type_: type) -> typing.Any:
    if type_ is bool:
        if value == "False":
            return False
        if value == "True":
            return True
        raise TypeError
    return type_(value)


def test_write_form_8949_multiple_rows(tmp_path):
    rows = [
        main.Form8949Row(1971, True, "0.00439 ETH", "01/01/1970", "01/02/1971", 0, 2),
        main.Form8949Row(1971, False, "1.00439 ETH", "12/31/1970", "01/02/1971", 43, 0),
    ]
    file_path = tmp_path / "form-8949.csv"
    main.Form8949File(rows).write_to_file(file_path)
    rows = collections.deque(rows)
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Cast values in row
            for field in dataclasses.fields(main.Form8949Row):
                row[field.name] = cast_string(row[field.name], field.type)
            assert main.Form8949Row(**row) == rows.popleft()
    assert len(rows) == 0


@pytest.mark.parametrize(
    ["spent_eth", "form_row"],
    [
        (
            main.SpentETH(
                datetime.datetime(1967, 2, 28, 23, 59, 59),
                datetime.datetime(1968, 2, 29),
                0.0004,
                1,
                0,
            ),
            main.Form8949Row(
                1968, True, "0.0004 ETH", "02/28/1967", "02/29/1968", 0, 1
            ),
        ),
        (
            main.SpentETH(
                datetime.datetime(2004, 2, 29),
                datetime.datetime(2005, 2, 28, 23, 59, 59),
                34.0,
                5000,
                4930,
            ),
            main.Form8949Row(
                2005, False, "34.0 ETH", "02/29/2004", "02/28/2005", 4930, 5000
            ),
        ),
        (
            main.SpentETH(
                datetime.datetime(3004, 2, 29),
                datetime.datetime(3005, 3, 1),
                0.0,
                1,
                0,
            ),
            main.Form8949Row(3005, True, "0.0 ETH", "02/29/3004", "03/01/3005", 0, 1),
        ),
    ],
)
def test_convert_spent_eth_to_form_8949_row(
    spent_eth: main.SpentETH, form_row: main.Form8949Row
):
    assert spent_eth.convert_to_form_8949_row() == form_row


def test_convert_acquired_eth_to_spent_eth():
    acquired_eth = main.AcquiredETH(
        datetime.datetime(2022, 3, 13, 20, 10, 59), 3.5831789, 2570.75
    )
    time_spent = datetime.datetime(2022, 3, 13, 20, 11, 2)
    proceeds_usd_excluding_fees = 6039
    spent_eth = main.SpentETH(
        datetime.datetime(2022, 3, 13, 20, 10, 59),
        time_spent,
        3.5831789,
        int(3.5831789 * 2570.75),
        proceeds_usd_excluding_fees,
    )
    assert (
        acquired_eth.convert_to_spent_eth(time_spent, proceeds_usd_excluding_fees)
        == spent_eth
    )
