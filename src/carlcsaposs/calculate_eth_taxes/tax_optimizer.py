"""
tax_optimizer: Sort list of 'AcquiredETH' for a tax optimization method

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
import abc

from . import currency
from . import exchange_transactions
from . import utils


class OptimizationMethod(abc.ABC):
    """Transaction processing mode for a tax year"""

    @staticmethod
    @abc.abstractmethod
    def sort(
        acquired_eths: list[currency.AcquiredETH],
        transaction: exchange_transactions.Spend,
    ) -> list[currency.AcquiredETH]:
        """Sort list of 'AcquiredETH' in order of least to most tax optimal

        Most tax optimal is the last item
        Least tax optimal is the first item
        """


class FirstInFirstOut(OptimizationMethod):
    """Spend ETH in the order it was purchased

    Kept for backwards compatability and to support using other tax
    calculation methods in other years
    """

    @staticmethod
    def sort(
        acquired_eths: list[currency.AcquiredETH], _: exchange_transactions.Spend
    ) -> list[currency.AcquiredETH]:
        """Sort list of 'AcquiredETH' in reverse chronological order

        First in is the last item
        Last in is the first item
        """
        return sorted(
            acquired_eths,
            key=lambda acquired_eth: acquired_eth.time_acquired,
            reverse=True,
        )


def _separate_acquired_eths(
    acquired_eths: list[currency.AcquiredETH], transaction: exchange_transactions.Spend
) -> tuple[
    list[currency.AcquiredETH], list[currency.AcquiredETH], list[currency.AcquiredETH]
]:
    """Separate list of 'AcquiredETH' by time and gain"""
    long_term = []
    short_term_gains = []
    short_term_non_gains = []  # loss or net zero
    for acquired_eth in acquired_eths:
        if utils.is_long_term(acquired_eth.time_acquired, transaction.time):
            long_term.append(acquired_eth)
        elif (
            transaction.proceeds_us_cents_per_eth_excluding_fees
            > acquired_eth.cost_us_cents_per_eth_including_fees
        ):
            short_term_gains.append(acquired_eth)
        else:
            short_term_non_gains.append(acquired_eth)
    return long_term, short_term_gains, short_term_non_gains


class LowerTaxBracket(OptimizationMethod):
    """Optimize for long-term capital gains, then higher taxes for year

    For US federal taxes, long-term capital gains are taxed at a lower
    rate than short-term capital gains.

    If taxpayer is in a lower tax bracket than they expect to be in
    future years, they can use this strategy to realize a greater
    capital gain (and pay more taxes) now.
    """

    @staticmethod
    def sort(
        acquired_eths: list[currency.AcquiredETH],
        transaction: exchange_transactions.Spend,
    ) -> list[currency.AcquiredETH]:
        """Sort list of 'AcquiredETH' for lower than normal tax bracket

        Segment 3 of 3: short-term non-gains
        Latest short-term non-gain is the last item
        Earliest short-term non-gain is the first item
        Potentially enables a future gain to be long-term instead of
        short-term; short-term losses offset short-term gains

        Segment 2 of 3: long-term
        Cheapest (highest gain) is the last item
        Most expensive (lowest gain) is the first item
        Any long-term gain or loss is better than a short-term gain.

        Segment 1 of 3: short-term gains
        Latest short-term gain is the last item
        Earliest short-term gain is the first item
        Potentially enables a future gain to be long-term instead of
        short-term
        """
        long_term, short_term_gains, short_term_non_gains = _separate_acquired_eths(
            acquired_eths, transaction
        )
        short_term_non_gains.sort(key=lambda acquired_eth: acquired_eth.time_acquired)
        long_term.sort(
            key=lambda acquired_eth: acquired_eth.cost_us_cents_per_eth_including_fees,
            reverse=True,
        )
        short_term_gains.sort(key=lambda acquired_eth: acquired_eth.time_acquired)
        return short_term_gains + long_term + short_term_non_gains


class HigherTaxBracket(OptimizationMethod):
    """Optimize for long-term capital gains, then lower taxes for year

    For US federal taxes, long-term capital gains are taxed at a lower
    rate than short-term capital gains.

    If taxpayer is in a higher tax bracket than they expect to be in
    future years, they can use this strategy to realize a lower
    capital gain (and pay less taxes) now.
    """

    @staticmethod
    def sort(
        acquired_eths: list[currency.AcquiredETH],
        transaction: exchange_transactions.Spend,
    ) -> list[currency.AcquiredETH]:
        """Sort list of 'AcquiredETH' for higher than normal tax bracket

        Segment 3 of 3: short-term non-gains
        Latest short-term non-gain is the last item
        Earliest short-term non-gain is the first item
        Potentially enables a future gain to be long-term instead of
        short-term; short-term losses offset short-term gains

        Segment 2 of 3: long-term
        Most expensive (lowest gain) is the last item
        Cheapest (highest gain) is the first item
        Any long-term gain or loss is better than a short-term gain.

        Segment 1 of 3: short-term gains
        Latest short-term gain is the last item
        Earliest short-term gain is the first item
        Potentially enables a future gain to be long-term instead of
        short-term
        """
        long_term, short_term_gains, short_term_non_gains = _separate_acquired_eths(
            acquired_eths, transaction
        )
        short_term_non_gains.sort(key=lambda acquired_eth: acquired_eth.time_acquired)
        long_term.sort(
            key=lambda acquired_eth: acquired_eth.cost_us_cents_per_eth_including_fees
        )
        short_term_gains.sort(key=lambda acquired_eth: acquired_eth.time_acquired)
        return short_term_gains + long_term + short_term_non_gains
