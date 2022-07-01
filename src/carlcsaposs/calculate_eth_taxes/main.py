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
from . import file_reader
from . import file_writer
from . import transaction_processor
from . import user_input


EXCHANGE_TRANSACTIONS = file_reader.read_files(
    user_input.ETHERSCAN_TRANSACTION_CSVS,
    user_input.COINBASE_CSV,
    user_input.COINBASE_PRO_ACCOUNT_CSV,
    user_input.BLOCKLISTED_COINBASE_PRO_TRANSFER_IDS,
)

SPENT_ETHS = transaction_processor.convert_transactions_to_spent_eth(
    EXCHANGE_TRANSACTIONS, user_input.TAX_MODES_BY_YEAR
)

ROWS = [spent_eth.convert_to_form_8949_row() for spent_eth in SPENT_ETHS]

file_writer.Form8949File(ROWS).write_to_file("output.csv")
