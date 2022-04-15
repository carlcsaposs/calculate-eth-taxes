# pylint: disable=missing-docstring
import csv
import dataclasses
import datetime
import decimal
import enum
import typing

from . import file_writer
from . import exchange_transactions
from . import transaction_processor
from . import user_input
from . import utils


@dataclasses.dataclass
class WalletTransaction:

    time: datetime.datetime
    wallet_from: str
    wallet_to: str
    # Wei: 10^-18 ETH
    amount_wei: int
    fee_wei: int
    us_cents_per_eth: int

    def __post_init__(self):
        self.wallet_from = self.wallet_from.lower()
        self.wallet_to = self.wallet_to.lower()

    def convert_fee_to_spend_transaction(self) -> exchange_transactions.Spend:
        return exchange_transactions.Spend(self.time, self.fee_wei, 0)

    def convert_amount_to_spend_transaction(self) -> exchange_transactions.Spend:
        return exchange_transactions.Spend(
            self.time, self.amount_wei, self.us_cents_per_eth
        )


WALLET_TRANSACTIONS_BY_WALLET: dict[str, list[WalletTransaction]] = {}

for file_name in user_input.ETHERSCAN_TRANSACTION_CSVS:
    with open(
        f"/home/user/QubesIncoming/files/calculate-eth-taxes/input/{file_name}",
        "r",
        encoding="utf-8",
    ) as file:
        wallet_address = file_name.split("-")[1].split(".")[0].lower()
        assert len(wallet_address) == 42
        WALLET_TRANSACTIONS_BY_WALLET[wallet_address] = []
        for row in csv.DictReader(file):

            def convert_eth_to_wei(amount_eth: str) -> int:
                return utils.round_decimal_to_int(
                    decimal.Decimal(amount_eth) * 10**18
                )

            amount_in = convert_eth_to_wei(row["Value_IN(ETH)"])
            amount_out = convert_eth_to_wei(row["Value_OUT(ETH)"])
            assert amount_in == 0 or amount_out == 0
            amount_wei = amount_in or amount_out
            # Check for error
            if row["Status"] == "Error(0)" and row["ErrCode"] == "Out of gas":
                # If there is an error, no ETH will be transferred but the fee will still be lost
                amount_wei = 0
            # Override for internal transaction
            elif (
                row["Txhash"]
                == "0x6f0b139844b33d88d6ee6acedfb8cf4ba1f5d6e8b9d85d91d14ab238a9f8a443"
            ):
                amount_wei -= 2837798149744091
                assert amount_wei == 56755962994881820
            else:
                assert row["Status"] == "" and row["ErrCode"] == ""
            WALLET_TRANSACTIONS_BY_WALLET[wallet_address].append(
                WalletTransaction(
                    datetime.datetime.fromtimestamp(int(row["UnixTimestamp"])),
                    row["From"],
                    row["To"],
                    amount_wei,
                    utils.round_decimal_to_int(
                        decimal.Decimal(row["TxnFee(ETH)"]) * 10**18
                    ),
                    utils.round_decimal_to_int(
                        decimal.Decimal(row["Historical $Price/Eth"]) * 100
                    ),
                )
            )


@dataclasses.dataclass
class CoinbaseTransferTransaction:
    class TransactionType(enum.Enum):
        FROM_COINBASE = enum.auto()
        TO_COINBASE = enum.auto()

    time: datetime.datetime
    amount_wei: int
    type_: TransactionType


def convert_coinbase_timestamp_to_datetime(
    coinbase_timestamp: str,
) -> datetime.datetime:
    return datetime.datetime.strptime(coinbase_timestamp, "%Y-%m-%dT%H:%M:%SZ")


def convert_coinbase_pro_timestamp_to_datetime(
    coinbase_pro_timestamp: str,
) -> datetime.datetime:
    return datetime.datetime.strptime(coinbase_pro_timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")


COINBASE_TRANSFER_TRANSACTIONS: list[CoinbaseTransferTransaction] = []

EXCHANGE_TRANSACTIONS: list[exchange_transactions.CurrencyExchange] = []

with open(
    f"/home/user/QubesIncoming/files/calculate-eth-taxes/input/{user_input.COINBASE_CSV}",
    "r",
    encoding="utf-8",
) as file:
    for row in csv.DictReader(file):
        assert row["Asset"] == "ETH"
        time = convert_coinbase_timestamp_to_datetime(row["Timestamp"])
        amount_eth = decimal.Decimal(row["Quantity Transacted"])
        amount_wei = utils.round_decimal_to_int(amount_eth * 10**18)
        if row["Transaction Type"] == "Buy":

            EXCHANGE_TRANSACTIONS.append(
                exchange_transactions.Acquire(
                    time,
                    amount_wei,
                    utils.round_decimal_to_int(
                        decimal.Decimal(row["Total (inclusive of fees)"])
                        * 100
                        / amount_eth
                    ),
                )
            )
        elif row["Transaction Type"] == "Sell":
            raise NotImplementedError
        elif row["Transaction Type"] == "Send":
            COINBASE_TRANSFER_TRANSACTIONS.append(
                CoinbaseTransferTransaction(
                    time,
                    amount_wei,
                    CoinbaseTransferTransaction.TransactionType.FROM_COINBASE,
                )
            )
        elif row["Transaction Type"] == "Receive":
            COINBASE_TRANSFER_TRANSACTIONS.append(
                CoinbaseTransferTransaction(
                    time,
                    amount_wei,
                    CoinbaseTransferTransaction.TransactionType.TO_COINBASE,
                )
            )
        else:
            raise ValueError

coinbase_pro_rows: list[dict[str, str]] = []
with open(
    f"/home/user/QubesIncoming/files/calculate-eth-taxes/input/{user_input.COINBASE_PRO_ACCOUNT_CSV}",
    "r",
    encoding="utf-8",
) as file:
    for row in csv.DictReader(file):
        if row["transfer id"] in user_input.BLOCKLISTED_COINBASE_PRO_TRANSFER_IDS:
            continue
        coinbase_pro_rows.append(row)


class CoinbaseProOrderMatchRow:
    class Unit(enum.Enum):
        ETH = enum.auto()
        USD = enum.auto()

    order_id: str
    time: datetime.datetime
    amount: decimal.Decimal
    unit: Unit

    def __init__(self, row: dict[str, str]):
        self.order_id = row["order id"]
        self.time = convert_coinbase_pro_timestamp_to_datetime(row["time"])
        self.amount = decimal.Decimal(row["amount"])
        self.unit = self.Unit[row["amount/balance unit"]]


last_order_id_first_index: typing.Optional[int] = None
for index, row in enumerate(coinbase_pro_rows):
    # Exchange USD for ETH or vice versa
    if row["order id"] != "":
        if last_order_id_first_index is None:
            assert row["type"] == "match"
            last_order_id_first_index = index
        if row["type"] == "match":
            continue

        assert row["type"] == "fee"
        first_match_order = CoinbaseProOrderMatchRow(coinbase_pro_rows[index - 2])
        second_match_order = CoinbaseProOrderMatchRow(coinbase_pro_rows[index - 1])
        assert (
            first_match_order.order_id == second_match_order.order_id == row["order id"]
        )
        assert first_match_order.time == second_match_order.time
        assert first_match_order.amount < 0 and second_match_order.amount > 0
        # USD for ETH
        if first_match_order.unit == CoinbaseProOrderMatchRow.Unit.USD:
            assert second_match_order.unit == CoinbaseProOrderMatchRow.Unit.ETH
            amount_wei = utils.round_decimal_to_int(
                second_match_order.amount * 10**18
            )
            cost_us_cents_per_eth_including_fees = utils.round_decimal_to_int(
                -first_match_order.amount * 100 / second_match_order.amount
            )
            EXCHANGE_TRANSACTIONS.append(
                exchange_transactions.Acquire(
                    second_match_order.time,
                    amount_wei,
                    cost_us_cents_per_eth_including_fees,
                )
            )
        # ETH for USD
        elif first_match_order.unit == CoinbaseProOrderMatchRow.Unit.ETH:
            assert second_match_order.unit == CoinbaseProOrderMatchRow.Unit.USD
            amount_wei = utils.round_decimal_to_int(
                -first_match_order.amount * 10**18
            )
            fee = decimal.Decimal(row["amount"])
            assert fee < 0
            proceeds_us_cents_per_eth_excluding_fees = utils.round_decimal_to_int(
                (second_match_order.amount + fee) * 100 / (-first_match_order.amount)
            )
            EXCHANGE_TRANSACTIONS.append(
                exchange_transactions.Spend(
                    second_match_order.time,
                    amount_wei,
                    proceeds_us_cents_per_eth_excluding_fees,
                )
            )
        last_order_id_first_index = None
        continue

    assert row["type"] in ["withdrawal", "deposit"]
    if row["amount/balance unit"] == "USD":
        continue
    assert row["amount/balance unit"] == "ETH"
    time = convert_coinbase_pro_timestamp_to_datetime(row["time"])
    amount_wei = utils.round_decimal_to_int(decimal.Decimal(row["amount"]) * 10**18)
    if row["type"] == "withdrawal":
        amount_wei = -amount_wei
        type_ = CoinbaseTransferTransaction.TransactionType.FROM_COINBASE
    elif row["type"] == "deposit":
        type_ = CoinbaseTransferTransaction.TransactionType.TO_COINBASE
    assert amount_wei > 0
    COINBASE_TRANSFER_TRANSACTIONS.append(
        CoinbaseTransferTransaction(time, amount_wei, type_)
    )

COINBASE_TRANSFER_TRANSACTIONS = sorted(
    COINBASE_TRANSFER_TRANSACTIONS, key=lambda transaction: transaction.time
)
for coinbase_transaction in COINBASE_TRANSFER_TRANSACTIONS:
    for wallet_address, transactions in WALLET_TRANSACTIONS_BY_WALLET.items():
        for transaction in transactions:
            amount_wei = transaction.amount_wei
            if (
                coinbase_transaction.type_
                == CoinbaseTransferTransaction.TransactionType.FROM_COINBASE
            ):
                amount_wei += transaction.fee_wei
            if abs(
                amount_wei
                - coinbase_transaction.amount_wei
                # 1000000000000000 wei = .001 ETH
            ) < 1000000000000000 and abs(
                transaction.time - coinbase_transaction.time
            ) < datetime.timedelta(
                minutes=15
            ):
                if (
                    coinbase_transaction.type_
                    == CoinbaseTransferTransaction.TransactionType.FROM_COINBASE
                ):
                    transaction.wallet_from = "coinbase"
                elif (
                    coinbase_transaction.type_
                    == CoinbaseTransferTransaction.TransactionType.TO_COINBASE
                ):
                    transaction.wallet_to = "coinbase"
                else:
                    raise ValueError
                break
        else:
            continue
        break
    else:
        if (
            coinbase_transaction.time == datetime.datetime(2021, 1, 2, 19, 37, 5)
            and coinbase_transaction.amount_wei == 76506000000000000
            and coinbase_transaction.type_
            == CoinbaseTransferTransaction.TransactionType.FROM_COINBASE
        ):
            EXCHANGE_TRANSACTIONS.append(
                exchange_transactions.Spend(
                    coinbase_transaction.time,
                    coinbase_transaction.amount_wei,
                    utils.round_decimal_to_int(5992 / decimal.Decimal("0.076506")),
                )
            )
        else:
            raise ValueError
WALLET_ADDRESSES = list(WALLET_TRANSACTIONS_BY_WALLET.keys())
WALLET_ADDRESSES.append("coinbase")

for wallet_address, transactions in WALLET_TRANSACTIONS_BY_WALLET.items():
    for transaction in transactions:
        if transaction.wallet_to == wallet_address:
            if transaction.wallet_from not in WALLET_ADDRESSES:
                raise NotImplementedError(
                    "ETH acquistion outside of Coinbase not supported"
                )
            elif transaction.wallet_from != "coinbase":
                continue
        assert wallet_address in WALLET_ADDRESSES
        if transaction.wallet_to not in WALLET_ADDRESSES:
            if transaction.amount_wei != 0:
                EXCHANGE_TRANSACTIONS.append(
                    transaction.convert_amount_to_spend_transaction()
                )
        EXCHANGE_TRANSACTIONS.append(transaction.convert_fee_to_spend_transaction())

spent_eths = transaction_processor.convert_transactions_to_spent_eth(
    EXCHANGE_TRANSACTIONS, user_input.TAX_MODES_BY_YEAR
)

rows = [spent_eth.convert_to_form_8949_row() for spent_eth in spent_eths]
print(sum([row.proceeds_usd - row.cost_usd for row in rows if row.tax_year == 2021]))

file_writer.Form8949File(rows).write_to_file("output.csv")