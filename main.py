"""
calculate-eth-taxes: generate Form 8949 data for US taxes on ETH

Copyright (C) 2021 Carl Csaposs

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
# Enable use of class type annotation inside its own class definition
from __future__ import annotations

import csv
import datetime
import typing


class Transaction:
    def __init__(self, timestamp: int):
        self.timestamp = timestamp


class InputTransaction(Transaction):
    """Buy ETH with USD"""

    def __init__(self, timestamp: int, wallet_to: str, usd_in: float, eth_out: float):
        super().__init__(timestamp)
        self.wallet_to = wallet_to
        self.usd_in = usd_in  # Includes fees
        self.eth_out = eth_out  # Does not include fees


class OutputTransaction(Transaction):
    """Sell ETH for USD

    Includes transfers (the fee is ETH sold for USD)"""

    def __init__(
        self,
        timestamp: int,
        wallet_from: str,
        amount_eth: float,
        eth_fee: float,
        historical_usd_price_per_eth: float,
    ):
        super().__init__(timestamp)
        self.wallet_from = wallet_from
        self.amount_eth = amount_eth
        self.eth_fee = eth_fee
        self.historical_usd_price_per_eth = historical_usd_price_per_eth

    def calculate_total_eth_in(self) -> float:
        """Return total ETH input (including fee) to transaction"""
        return self.amount_eth + self.eth_fee


class TransferTransaction(OutputTransaction):
    """Transfer ETH between wallets

    Fee is sold for USD"""

    def __init__(
        self,
        timestamp: int,
        wallet_from: str,
        wallet_to: str,
        amount_eth: float,
        eth_fee: float,
        historical_usd_price_per_eth: float,
    ):
        super().__init__(
            timestamp,
            wallet_from,
            amount_eth,
            eth_fee,
            historical_usd_price_per_eth,
        )
        self.wallet_to = wallet_to


class Input:
    """ETH purchased with USD"""

    def __init__(self, timestamp_purchased, usd_in, eth_out):
        self.timestamp_purchased = timestamp_purchased
        # "usd_in" includes fees
        self.avg_price_usd_per_eth = usd_in / eth_out
        self.eth_out = eth_out

    def calculate_usd_in(self) -> float:
        """Return current USD in"""
        return self.avg_price_usd_per_eth * self.eth_out

    def remove_eth(self, amount_eth: float) -> Input:
        """Remove part of the input

        Return amount removed as a new Input"""
        assert amount_eth > 0
        self.eth_out -= amount_eth
        assert self.eth_out > 0
        return Input(
            self.timestamp_purchased,
            self.avg_price_usd_per_eth * amount_eth,
            amount_eth,
        )


class SpentInput(Input):
    """Input (ETH) that has been sold for USD"""

    def __init__(self, input_: Input, timestamp_sold: int, usd_out: float):
        """Convert Input into SpentInput"""
        super().__init__(
            input_.timestamp_purchased,
            input_.calculate_usd_in(),
            input_.eth_out,
        )
        self.timestamp_sold = timestamp_sold
        self.usd_out = usd_out


class Wallet:
    """Hold ETH inputs"""

    def __init__(self):
        self.inputs = []

    def add_input(self, input_: Input) -> None:
        """Add ETH input to wallet"""
        self.inputs.append(input_)

    def remove_eth(self, amount_eth: float) -> typing.List[Input]:
        """Remove ETH from inputs using first in, first out

        Return list of inputs removed"""
        removed_inputs = []
        while amount_eth > 0:
            first_input = self.inputs[0]
            if amount_eth < first_input.eth_out:
                # Remove part of input
                removed_inputs.append(first_input.remove_eth(amount_eth))
                amount_eth = 0
            else:
                # Remove entirety of input
                removed_inputs.append(first_input)
                amount_eth -= first_input.eth_out
                self.inputs.pop(0)
        return removed_inputs


# User input
LEDGER_CSV = input("Relative file path to ledger CSV (ledger.csv): ") or "ledger.csv"
print("\nSeparate each address with a new line")
WALLET_ADDRESSES_FILE = (
    input("Relative file path to hardware wallet addresses (wallets.txt): ")
    or "wallets.txt"
)
SPENT_INPUTS_CSV = (
    input("\nRelative file path to export CSV (spent-inputs.csv): ")
    or "spent-inputs.csv"
)

MY_WALLET_ADDRESSES = ["Coinbase"]
with open(WALLET_ADDRESSES_FILE, "r") as file:
    for line in file.read().splitlines():
        if line != "":
            MY_WALLET_ADDRESSES.append(line)
# ETH addresses are case-insensitive
MY_WALLET_ADDRESSES = [address.lower() for address in MY_WALLET_ADDRESSES]

# Convert ledger CSV to list of Transaction objects
TRANSACTIONS: typing.List[Transaction] = []
with open(LEDGER_CSV, "r") as file:
    for row in csv.DictReader(file):
        if row["type"] == "input":
            TRANSACTIONS.append(
                InputTransaction(
                    int(row["timestamp"]),
                    # ETH addresses are case-insensitive
                    row["wallet_to"].lower(),
                    float(row["usd_in"]),
                    float(row["eth_out"]),
                )
            )
        elif row["type"] == "output":
            if row["wallet_to"].lower() in MY_WALLET_ADDRESSES:
                TRANSACTIONS.append(
                    TransferTransaction(
                        int(row["timestamp"]),
                        # ETH addresses are case-insensitive
                        row["wallet_from"].lower(),
                        row["wallet_to"].lower(),
                        float(row["amount_eth"]),
                        float(row["eth_fee"]),
                        float(row["historical_usd_price_per_eth"]),
                    )
                )
            else:
                TRANSACTIONS.append(
                    OutputTransaction(
                        int(row["timestamp"]),
                        # ETH addresses are case-insensitive
                        row["wallet_from"].lower(),
                        float(row["amount_eth"]),
                        float(row["eth_fee"]),
                        float(row["historical_usd_price_per_eth"]),
                    )
                )
        else:
            raise ValueError()
# Process transactions
SPENT_INPUTS: typing.List[SpentInput] = []
WALLETS = {address: Wallet() for address in MY_WALLET_ADDRESSES}
for transaction in TRANSACTIONS:
    if isinstance(transaction, InputTransaction):
        receiver = WALLETS[transaction.wallet_to]
        receiver.add_input(
            Input(transaction.timestamp, transaction.usd_in, transaction.eth_out)
        )
    elif isinstance(transaction, TransferTransaction):
        sender = WALLETS[transaction.wallet_from]
        receiver = WALLETS[transaction.wallet_to]
        # Take out fee from sender
        for input_ in sender.remove_eth(transaction.eth_fee):
            SPENT_INPUTS.append(SpentInput(input_, transaction.timestamp, 0))
        # Move amount from sender to receiver
        for input_ in sender.remove_eth(transaction.amount_eth):
            receiver.add_input(input_)
    elif isinstance(transaction, OutputTransaction):
        sender = WALLETS[transaction.wallet_from]
        # Take out fee from sender
        for input_ in sender.remove_eth(transaction.eth_fee):
            SPENT_INPUTS.append(SpentInput(input_, transaction.timestamp, 0))
        # Take out amount from sender
        for input_ in sender.remove_eth(transaction.amount_eth):
            SPENT_INPUTS.append(
                SpentInput(
                    input_,
                    transaction.timestamp,
                    input_.eth_out * transaction.historical_usd_price_per_eth,
                )
            )
    else:
        raise ValueError()
# Export spent inputs to CSV
with open(SPENT_INPUTS_CSV, "w") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=[
            "tax_year",
            "is_long_term",
            "description",
            "date_acquired",
            "date_sold",
            "usd_out",
            "usd_in",
        ],
    )
    writer.writeheader()
    for spent_input in SPENT_INPUTS:
        acquired = datetime.datetime.fromtimestamp(spent_input.timestamp_purchased)
        sold = datetime.datetime.fromtimestamp(spent_input.timestamp_sold)
        writer.writerow(
            {
                "tax_year": sold.year,
                # Long term is one calendar year or more not including the date of acquisition
                # (or more than one calendar year including the date of acquisition)
                "is_long_term": acquired.date().replace(year=acquired.year + 1)
                < sold.date(),
                "description": f"{spent_input.eth_out} ETH",
                "date_acquired": acquired.strftime("%m/%d/%Y"),
                "date_sold": sold.strftime("%m/%d/%Y"),
                "usd_out": spent_input.usd_out,
                "usd_in": spent_input.calculate_usd_in(),
            }
        )
print(f"\nSpent inputs exported to {SPENT_INPUTS_CSV}")
