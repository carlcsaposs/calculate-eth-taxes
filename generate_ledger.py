"""
generate-ledger: generate ETH ledger for calculate-eth-taxes

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
import bisect
import csv
import datetime


def convert_timestamp_to_unix_time(timestamp: str) -> int:
    """Convert timestamp string in Coinbase CSV export to unix time"""
    unix_time = int(
        (
            datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
            - datetime.datetime(1970, 1, 1)
        ).total_seconds()
    )
    assert unix_time > 0
    return unix_time


def find_closest_coinbase_transaction(etherscan_transaction, coinbase_transactions):
    """Find Coinbase transaction which has the closest timestamp to Etherscan.io transaction"""
    closest_transaction_type = ""
    closest_transaction = {"timestamp": 0}
    for transaction_type, coinbase_transactions in coinbase_transactions.items():
        coinbase_transaction_timestamps = [
            transaction["timestamp"] for transaction in coinbase_transactions
        ]
        # Transactions are sorted chronologically
        # Find index of closest Coinbase transaction after Etherscan.io transaction
        closest_transaction_after_index = bisect.bisect(
            coinbase_transaction_timestamps,
            etherscan_transaction["timestamp"],
        )
        # Find index of closest Coinbase transaction before Etherscan.io transaction
        closest_transaction_before_index = closest_transaction_after_index - 1

        for index in [
            closest_transaction_after_index,
            closest_transaction_before_index,
        ]:
            # Check if index is valid
            if 0 <= index < len(coinbase_transaction_timestamps):
                coinbase_transaction = coinbase_transactions[index]
                # Check if closer than current closest transaction
                if abs(
                    coinbase_transaction["timestamp"]
                    - etherscan_transaction["timestamp"]
                ) < abs(
                    closest_transaction["timestamp"]
                    - etherscan_transaction["timestamp"]
                ):
                    # Update closest transaction
                    closest_transaction = coinbase_transaction
                    closest_transaction_type = transaction_type
    assert closest_transaction["timestamp"] != 0
    return closest_transaction_type, closest_transaction


# User input
COINBASE_CSV = (
    input("Relative file path to Coinbase CSV (coinbase.csv): ") or "coinbase.csv"
)
ETHERSCAN_CSVS = []
print("\nPress enter when done")
while True:
    path = input("Relative file path to etherscan.io CSV: ")
    if path == "":
        break
    ETHERSCAN_CSVS.append(path)
LEDGER_CSV = input("\nRelative file path to export CSV (ledger.csv): ") or "ledger.csv"

TRANSACTIONS = []
# Temporarily store Coinbase external transactions to correlate wallet addresses in
# etherscan.io transactions with Coinbase (since Coinbase rotates wallet addresses).
# Note: external transactions do not include ETH to USD or USD to ETH transactions
# Also, the Coinbase CSV doesn't have complete transaction data. To obtain missing
# data, correlate receive transactions from etherscan.io with Coinbase sends.
COINBASE_TRANSACTIONS = {
    "send": [],
    "receive": [],
}
# Import Coinbase CSV data
with open(COINBASE_CSV, "r") as file:
    for row in csv.DictReader(file):
        assert row["Asset"] == "ETH"
        if row["Transaction Type"] == "Buy":
            TRANSACTIONS.append(
                {
                    "type": "input",
                    "timestamp": convert_timestamp_to_unix_time(row["Timestamp"]),
                    "wallet_to": "Coinbase",
                    "usd_in": float(row["USD Total (inclusive of fees)"]),
                    "eth_out": float(row["Quantity Transacted"]),
                }
            )
        elif row["Transaction Type"] == "Sell":
            raise NotImplementedError()
        elif row["Transaction Type"] == "Send":
            COINBASE_TRANSACTIONS["send"].append(
                {
                    "timestamp": convert_timestamp_to_unix_time(row["Timestamp"]),
                    "amount_eth": float(row["Quantity Transacted"]),
                }
            )
        elif row["Transaction Type"] == "Receive":
            COINBASE_TRANSACTIONS["receive"].append(
                {
                    "timestamp": convert_timestamp_to_unix_time(row["Timestamp"]),
                    "amount_eth": float(row["Quantity Transacted"]),
                }
            )
        else:
            raise ValueError()
# Import Etherscan.io CSV data
for etherscan_csv in ETHERSCAN_CSVS:
    with open(etherscan_csv, "r") as file:
        for row in csv.DictReader(file):
            # Etherscan.io CSVs list the amount of ETH as either an input or output
            eth_in = float(row["Value_IN(ETH)"])
            eth_out = float(row["Value_OUT(ETH)"])
            # Check that there is not an ETH input *and* an ETH output
            assert eth_in == 0 or eth_out == 0
            amount_eth = eth_in or eth_out
            # Check for error
            if row["Status"] == "Error(0)" and row["ErrCode"] == "Out of gas":
                # If there is an error, no ETH will be transferred but the fee will still be lost
                amount_eth = 0
            else:
                assert row["Status"] == "" and row["ErrCode"] == ""

            etherscan_transaction = {
                "type": "output",
                "timestamp": int(row["UnixTimestamp"]),
                "wallet_from": row["From"],
                "wallet_to": row["To"],
                "amount_eth": amount_eth,
                "eth_fee": float(row["TxnFee(ETH)"]),
                "historical_usd_price_per_eth": float(row["Historical $Price/Eth"]),
            }

            # Check if transaction correlates with any Coinbase transaction
            # Find Coinbase transaction with closest timestamp
            (
                closest_coinbase_transaction_type,
                closest_coinbase_transaction,
            ) = find_closest_coinbase_transaction(
                etherscan_transaction, COINBASE_TRANSACTIONS
            )
            # Check if timestamps are within 5 minutes
            if abs(
                closest_coinbase_transaction["timestamp"]
                - etherscan_transaction["timestamp"]
                < 300
            ):
                # Check if amount ETH is within .001 ETH
                if closest_coinbase_transaction_type == "send":
                    if (
                        abs(
                            closest_coinbase_transaction["amount_eth"]
                            - (
                                etherscan_transaction["amount_eth"]
                                + etherscan_transaction["eth_fee"]
                            )
                        )
                        < 0.001
                    ):
                        etherscan_transaction["wallet_from"] = "Coinbase"
                elif closest_coinbase_transaction_type == "receive":
                    if (
                        abs(
                            closest_coinbase_transaction["amount_eth"]
                            - etherscan_transaction["amount_eth"]
                        )
                        < 0.001
                    ):
                        etherscan_transaction["wallet_to"] = "Coinbase"
                else:
                    raise ValueError()
            # Only add output transactions to avoid adding transactions twice
            if eth_in == 0:
                TRANSACTIONS.append(etherscan_transaction)
            # Unless it is a input transaction from Coinbase
            # (since we only have the full data from the Etherscan.io CSV and not the
            # Coinbase CSV)
            elif eth_in > 0 and etherscan_transaction["wallet_from"] == "Coinbase":
                TRANSACTIONS.append(etherscan_transaction)
# Sort transactions by timestamp
TRANSACTIONS.sort(key=lambda transaction: transaction["timestamp"])
# Export ledger CSV
with open(LEDGER_CSV, "w") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=[
            "type",
            "timestamp",
            "wallet_from",
            "wallet_to",
            "usd_in",
            "eth_out",
            "amount_eth",
            "eth_fee",
            "historical_usd_price_per_eth",
        ],
    )
    writer.writeheader()
    writer.writerows(TRANSACTIONS)
print(f"\nLedger exported to {LEDGER_CSV}")
