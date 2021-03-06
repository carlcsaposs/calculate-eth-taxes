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
import pathlib
import typing

import pytest

import carlcsaposs.calculate_eth_taxes.file_writer as file_writer


@pytest.mark.parametrize(
    ["override_key", "override_value"], [("proceeds_usd", -3), ("cost_usd", -1)]
)
def test_form_8949_row_negative_integer(override_key: str, override_value: int):
    row_dict = {
        "tax_year": 103,
        "is_long_term": False,
        "description": "3.3 ETH",
        "date_acquired": "12/12/103",
        "date_sold": "12/21/103",
        "proceeds_usd": 0,
        "cost_usd": 0,
    }
    row_dict[override_key] = override_value
    with pytest.raises(ValueError) as exception_info:
        file_writer.Form8949Row(**row_dict)
    assert (
        str(exception_info.value)
        == f"expected '{override_key}' greater than or equal to zero, got {override_value} instead"
    )


def test_write_form_8949_zero_rows(tmp_path: pathlib.Path):
    file_path = tmp_path / "form-8949.csv"
    file_writer.Form8949File([]).write_to_file(file_path)
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        assert reader.fieldnames == file_writer.Form8949File.FIELDNAMES
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
        file_writer.Form8949Row(
            1971, True, "0.00439 ETH", "01/01/1970", "01/02/1971", 0, 2
        ),
        file_writer.Form8949Row(
            1971, False, "1.00439 ETH", "12/31/1970", "01/02/1971", 43, 0
        ),
    ]
    file_path = tmp_path / "form-8949.csv"
    file_writer.Form8949File(rows).write_to_file(file_path)
    rows = collections.deque(rows)
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Cast values in row
            for field in dataclasses.fields(file_writer.Form8949Row):
                row[field.name] = cast_string(row[field.name], field.type)
            assert file_writer.Form8949Row(**row) == rows.popleft()
    assert len(rows) == 0
