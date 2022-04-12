"""
exchange_transactions:  Currency exchange transactions (ETH for USD or vice versa)

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

from . import currency


@dataclasses.dataclass
class CurrencyExchange:
    """Exchange ETH for USD or vice versa"""

    time: datetime.datetime
    amount_wei: int  # Wei: 10^-18 ETH


@dataclasses.dataclass
class Acquire(CurrencyExchange):
    """USD to ETH"""

    cost_us_cents_per_eth_including_fees: int

    def convert_to_acquired_eth(self) -> currency.AcquiredETH:
        """Create 'AcquiredETH' instance for this transaction"""
        return currency.AcquiredETH(
            self.time, self.amount_wei, self.cost_us_cents_per_eth_including_fees
        )


@dataclasses.dataclass
class Spend(CurrencyExchange):
    """ETH to USD (including as fee)"""

    proceeds_us_cents_per_eth_excluding_fees: int
