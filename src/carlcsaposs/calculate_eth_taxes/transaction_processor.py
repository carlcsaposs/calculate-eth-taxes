"""
transaction_processor: Convert transactions to list of 'SpentETH'

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

from . import currency
from . import exchange_transactions
from . import tax_optimizer


@dataclasses.dataclass
class _TransactionProcessor:
    """Convert transactions to list of 'SpentETH'"""

    transactions: list[exchange_transactions.CurrencyExchange]
    tax_modes_by_year: dict[int, tax_optimizer.OptimizationMethod]

    def __post_init__(self):
        self._acquired_eths: list[currency.AcquiredETH]
        self._spent_eths: list[currency.SpentETH]

    def sort_transactions_in_chronologial_order(self):
        """Sort transactions from oldest to newest"""
        self.transactions.sort(key=lambda transaction: transaction.time)

    def sort_acquired_eths(
        self,
        transaction: exchange_transactions.Spend,
    ):
        """Sort 'self._acquired_eths' from least to most tax optimal

        Most tax optimal is the last item
        Least tax optimal is the first item
        """
        tax_mode = self.tax_modes_by_year[transaction.time.year]
        self._acquired_eths = tax_mode.sort(self._acquired_eths, transaction)

    def remove_wei(self, transaction: exchange_transactions.Spend):
        """Remove ETH from end of list of 'self._acquired_eths'"""
        amount_wei = transaction.amount_wei
        while amount_wei > 0:
            if self._acquired_eths[-1].amount_wei > amount_wei:
                acquired_eth_to_convert = self._acquired_eths[-1].remove_wei(amount_wei)
            else:
                acquired_eth_to_convert = self._acquired_eths.pop()
            self._spent_eths.append(
                acquired_eth_to_convert.convert_to_spent_eth(
                    transaction.time,
                    transaction.proceeds_us_cents_per_eth_excluding_fees,
                )
            )
            amount_wei -= acquired_eth_to_convert.amount_wei

    @property
    def spent_eths(self) -> list[currency.SpentETH]:
        """Convert transactions to list of 'SpentETH'"""
        self.sort_transactions_in_chronologial_order()
        self._acquired_eths = []
        self._spent_eths = []
        for transaction in self.transactions:
            if isinstance(transaction, exchange_transactions.Acquire):
                self._acquired_eths.append(transaction.convert_to_acquired_eth())
            elif isinstance(transaction, exchange_transactions.Spend):
                self.sort_acquired_eths(transaction)
                self.remove_wei(transaction)
            else:
                raise ValueError()
        return self._spent_eths


def convert_transactions_to_spent_eth(
    transactions: list[exchange_transactions.CurrencyExchange],
    tax_modes_by_year: dict[int, tax_optimizer.OptimizationMethod],
) -> list[currency.SpentETH]:
    """Convert transactions to list of 'SpentETH'"""
    return _TransactionProcessor(transactions, tax_modes_by_year).spent_eths
