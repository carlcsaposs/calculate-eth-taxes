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
import datetime
import enum
import pathlib
import typing


class NumberDomain(enum.Enum):
    """Valid domain for a float or integer"""

    POSITIVE = (lambda x: x > 0, "greater than zero")
    NON_NEGATIVE = (lambda x: x >= 0, "greater than or equal to zero")


def validate_number_in_domain(
    key: str, number: typing.Union[int, float], domain: NumberDomain
):
    """Raise ValueError if number is not within domain"""
    if not domain.value[0](number):
        raise ValueError(f"expected '{key}' {domain.value[1]}, got {number} instead")


@dataclasses.dataclass(frozen=True)
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

    def __post_init__(self):
        for attribute in ["proceeds", "cost"]:
            validate_number_in_domain(
                attribute, getattr(self, attribute), NumberDomain.NON_NEGATIVE
            )


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


@dataclasses.dataclass
class SpentETH:
    """ETH that has been spent by taxpayer for USD (including as a fee)

    Even if the ETH was spent for something other than USD or sent to
    another person as ETH, it is viewed by the IRS as being spent by the
    taxpayer for its market value in USD.
    """

    time_acquired: datetime.datetime
    time_spent: datetime.datetime
    amount_eth: float  # TODO: consider using Decimal
    cost_usd_including_fees: int
    proceeds_usd_excluding_fees: int

    def __post_init__(self):
        for attribute in ["cost_usd_including_fees", "proceeds_usd_excluding_fees"]:
            validate_number_in_domain(
                attribute, getattr(self, attribute), NumberDomain.NON_NEGATIVE
            )
        validate_number_in_domain("amount_eth", self.amount_eth, NumberDomain.POSITIVE)
        if self.time_spent <= self.time_acquired:
            raise ValueError("'time_spent' must be after 'time_acquired'")

    def _is_long_term(self) -> bool:
        """Long term is one calendar year or more*

        *Does not include date of acquistion
        """
        # Including date of acquistion, long term is more than one
        # calendar year.
        acquired = self.time_acquired.date()
        spent = self.time_spent.date()
        try:
            acquired = acquired.replace(year=acquired.year + 1)
        except ValueError:
            if acquired.day == 29 and acquired.month == 2:
                # Leap day
                acquired = acquired.replace(year=acquired.year + 1, day=28)
            else:
                raise
        return acquired < spent

    def convert_to_form_8949_row(self) -> Form8949Row:
        """Convert to Form 8949 row"""
        return Form8949Row(
            self.time_spent.year,
            self._is_long_term(),
            f"{self.amount_eth} ETH",
            self.time_acquired.strftime("%m/%d/%Y"),
            self.time_spent.strftime("%m/%d/%Y"),
            self.proceeds_usd_excluding_fees,
            self.cost_usd_including_fees,
        )


@dataclasses.dataclass
class AcquiredETH:
    """ETH that has been acquired by taxpayer for USD

    Even if the ETH was acquired from something other than USD or sent
    from another person as ETH, it is viewed by the IRS as being
    acquired by the taxpayer for its market value in USD.
    """

    time_acquired: datetime.datetime
    amount_eth: float  # TODO: consider using Decimal
    cost_usd_per_eth_including_fees: float  # TODO: consider using Decimal

    def __post_init__(self):
        for attribute in ["amount_eth", "cost_usd_per_eth_including_fees"]:
            validate_number_in_domain(
                attribute, getattr(self, attribute), NumberDomain.POSITIVE
            )

    def convert_to_spent_eth(
        self, time_spent: datetime.datetime, proceeds_usd_excluding_fees: int
    ) -> SpentETH:
        """Convert to 'SpentETH'"""
        return SpentETH(
            self.time_acquired,
            time_spent,
            self.amount_eth,
            int(self.amount_eth * self.cost_usd_per_eth_including_fees),
            proceeds_usd_excluding_fees,
        )

    def remove_eth(self, amount_eth: float) -> "AcquiredETH":
        """Move ETH into new instance"""
        if not 0 < amount_eth < self.amount_eth:
            raise ValueError(
                f"expected value between 0.0 and {self.amount_eth}, got {amount_eth} instead"
            )
        self.amount_eth -= amount_eth
        return AcquiredETH(
            self.time_acquired, amount_eth, self.cost_usd_per_eth_including_fees
        )
