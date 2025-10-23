# Project Description
The project is a part of internship hiring process task assigned by Primetrade.ai
# PrimeTrade — Binance USDT-M Futures Trading Bot

A lightweight, CLI-based trading bot for Binance USDT-M Futures (Testnet) built as a hiring/task project. This repository demonstrates placing market and limit orders, an OCO helper, input validation, structured logging, and a dry-run simulation mode for safe testing.

Author: Harsh Murjani

## Features
- Place Market Orders (USDT-M Futures)
- Place Limit Orders (USDT-M Futures) with validation (price/tick, quantity/step)
- OCO (One-Cancels-the-Other) flow: entry → take-profit (limit) + stop-loss (stop market)
- Dry-run simulation mode (no API calls) via `--dry-run` and `DummyClient`
- Balance display (futures account balances)
- Structured logs written to `bot.log` with timestamps and error traces
- Input validation with helpful error messages

## Project Structure
```
[project_root]/
├── src/
│   ├── common.py        # Core bot utilities, client init, DummyClient
│   ├── market_order.py  # Market order logic and validation
│   ├── limit_order.py   # Limit order logic and validation
│   └── advance/
│       └── oco.py       # OCO helper (entry + TP + SL monitoring)
├── main.py              # CLI entrypoint
├── check_keys.py        # Quick key verifier for testnet credentials
├── .env                 # API credentials (not checked into git)
├── requirements.txt     # Python dependencies
└── bot.log              # Runtime logs (created when running)
```

## Requirements
- Python 3.8+ (tested with 3.9)
- Dependencies in `requirements.txt` (install with pip)

Install dependencies:
```bash
python3 -m pip install -r requirements.txt
```

## Configuration
1. Create a `.env` file at project root with your testnet API credentials:

```text
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
TESTNET=true
```

2. Use Binance Futures Testnet (demo/testnet) API keys. In the current Binance demo/testnet flow the same demo API key covers futures — ensure the key has reading and futures/trading enabled and no IP restrictions.

Note: Do NOT commit `.env` to source control. `.gitignore` already excludes it.

## Usage (CLI)
All commands use `main.py`. Basic pattern:

```bash
python3 main.py [--dry-run] <command> [args]
```

Available commands:

- balance
	- Show futures account balances
	- Example: `python3 main.py balance`

- market <symbol> <buy|sell> <quantity>
	- Place a market order
	- Example: `python3 main.py market BTCUSDT buy 0.001`

- limit <symbol> <buy|sell> <quantity> <price> [--time-in-force GTC|IOC|FOK]
	- Place a limit order
	- Example: `python3 main.py limit BTCUSDT sell 0.001 105000 --time-in-force GTC`

- oco <symbol> <buy|sell> <quantity> <price> <stop_price> <stop_limit_price>
	- Place an entry (market/limit) and then create TP (limit) + SL (stop-market).
	- Example: `python3 main.py oco BTCUSDT buy 0.001 105000 99000 98900`

Dry-run (simulate without API calls):
```bash
python3 main.py --dry-run market BTCUSDT buy 0.001
```

## How validation works
- Symbol validity is checked against exchange info from the client
- Quantity is validated/rounded to the symbol's LOT_SIZE step
- Price is validated/rounded to the symbol's PRICE_FILTER tickSize

If validation fails, the CLI prints a helpful error and logs details to `bot.log`.

## Troubleshooting
- Error: `APIError(code=-2015): Invalid API-key, IP, or permissions for action`
	- Cause: Using keys without futures permission or keys from a different environment.
	- Fixes:
		1. Ensure the API key is created from the Binance demo/testnet environment and has futures/trading enabled.
		2. Remove any IP restrictions on the test key while testing.
		3. Verify `.env` values and restart your shell/IDE.
		4. Use `python3 check_keys.py` to verify permissions and connectivity.

- API endpoint changes / testnet redirects
	- Binance testnet/demo routing sometimes redirects between `testnet.binance.vision`, `testnet.binancefuture.com`, and `demo.binance.com`.
	- The code configures the client at runtime to use the demo/testnet URLs so keys from demo should work.

## Logging
- Logs are written to `bot.log` in the project root. They include timestamped INFO and ERROR messages for requests, responses, and exceptions.

## Tests / Manual Verification
1. Dry-run quick test (no API keys needed):
```bash
python3 main.py --dry-run market BTCUSDT buy 0.001
```

2. Verify API keys (after populating `.env`):
```bash
python3 check_keys.py
```

3. Place a small market order (testnet):
```bash
python3 main.py market BTCUSDT buy 0.001
```

4. Place a limit order (testnet):
```bash
python3 main.py limit BTCUSDT sell 0.001 105000
```

## Notes & Limitations
- This project is intentionally small and focused for a hiring task. It is not production-ready.
- No wallet/secret management beyond `.env` — keep secrets safe.
- Risk controls, position sizing, order lifecycle reconciliation, and concurrency protections are out of scope for this task but are natural next steps.

## Next steps (recommended)
- Add unit tests for validation logic (quantity/price step rounding)
- Add a TWAP or grid strategy module for advanced order splitting
- Add better reconciliation and order state persistence (DB or file)

---
If you want, I can also prepare a short `report.pdf` with screenshots, explanation, and a sample run for submission.

Author: Harsh Murjani
