"""
currency: ETH acquired and/or spent by taxpayer

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
import dataclasses
import datetime
import decimal

from . import file_writer
from . import utils


@dataclasses.dataclass
class SpentETH:
    """ETH that has been spent by taxpayer for USD (including as a fee)

    Even if the ETH was spent for something other than USD or sent to
    another person as ETH, it is viewed by the IRS as being spent by the
    taxpayer for its market value in USD.
    """

    time_acquired: datetime.datetime
    time_spent: datetime.datetime
    amount_wei: int  # Wei: 10^-18 ETH
    cost_usd_including_fees: int
    proceeds_usd_excluding_fees: int

    def __post_init__(self):
        for attribute in ["cost_usd_including_fees", "proceeds_usd_excluding_fees"]:
            utils.NumberDomain.NON_NEGATIVE.validate_number(
                attribute, getattr(self, attribute)
            )
        utils.NumberDomain.POSITIVE.validate_number("amount_wei", self.amount_wei)
        if self.time_spent <= self.time_acquired:
            raise ValueError("'time_spent' must be after 'time_acquired'")

    def convert_to_form_8949_row(self) -> file_writer.Form8949Row:
        """Convert to Form 8949 row"""
        amount_eth = utils.round_decimal(
            self.amount_wei / decimal.Decimal(10**18), 18
        )
        return file_writer.Form8949Row(
            self.time_spent.year,
            utils.is_long_term(self.time_acquired, self.time_spent),
            f"{amount_eth} ETH",
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
    amount_wei: int  # Wei: 10^-18 ETH
    cost_us_cents_per_eth_including_fees: int

    def __post_init__(self):
        for attribute in ["amount_wei", "cost_us_cents_per_eth_including_fees"]:
            utils.NumberDomain.POSITIVE.validate_number(
                attribute, getattr(self, attribute)
            )

    def convert_to_spent_eth(
        self,
        time_spent: datetime.datetime,
        proceeds_us_cents_per_eth_excluding_fees: int,
    ) -> SpentETH:
        """Convert to 'SpentETH'"""
        return SpentETH(
            self.time_acquired,
            time_spent,
            self.amount_wei,
            utils.round_decimal_to_int(
                (self.amount_wei * self.cost_us_cents_per_eth_including_fees)
                / decimal.Decimal(100 * 10**18)
            ),  # 100 is cents to dollars, 10**18 is Wei to ETH
            utils.round_decimal_to_int(
                (self.amount_wei * proceeds_us_cents_per_eth_excluding_fees)
                / decimal.Decimal(100 * 10**18)
            ),  # 100 is cents to dollars, 10**18 is Wei to ETH
        )

    def remove_wei(self, amount_wei: int) -> "AcquiredETH":
        """Move ETH into new instance"""
        if not 0 < amount_wei < self.amount_wei:
            raise ValueError(
                f"expected value between 0 and {self.amount_wei}, got {amount_wei} instead"
            )
        self.amount_wei -= amount_wei
        return AcquiredETH(
            self.time_acquired, amount_wei, self.cost_us_cents_per_eth_including_fees
        )
