# calculate-eth-taxes
Generate Form 8949 data for US taxes on ETH

## Setup
```
sudo apt update
sudo apt install python3-venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Instructions
- Locate hardware wallet addresses
- For each address, export CSV of transactions from etherscan.io (start time range at first ever transaction date)
- Export Coinbase CSV & remove header
- Pass CSVs to generate_ledger.py
- Export internal transactions from etherscan.io and manually add to ledger (e.g. by subtracting from another output transaction)
- Pass ledger.csv file and wallet addresses to main.py