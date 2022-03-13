"""
calculate_eth_taxes: Generate Form 8949 data for US taxes on ETH

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
import csv
import dataclasses
import pathlib


@dataclasses.dataclass
class Form8949Row:
    """Row in Form 8949

    Represents ETH that has realized a capital gain in USD (includes
    ETH spent as fee)
    """

    tax_year: int
    is_long_term: bool
    description: str
    date_acquired: str
    date_sold: str
    proceeds: int
    cost: int


class Form8949File:
    """CSV file with format of IRS Form 8949"""

    FIELDNAMES = [field.name for field in dataclasses.fields(Form8949Row)]

    def __init__(self, rows: list[Form8949Row]):
        self.rows = rows

    def write_to_file(self, file_path: pathlib.Path) -> None:
        """Save instance to CSV file"""
        with open(file_path, "w", encoding="utf-8") as file:
            writer = csv.DictWriter(file, self.FIELDNAMES)
            writer.writeheader()
            for row in self.rows:
                writer.writerow(dataclasses.asdict(row))
