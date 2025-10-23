# Project Description
The project is a part of internship hiring process task assigned by Primetrade.ai
# PrimeTrade — Binance USDT-M Futures Trading Bot

A lightweight, CLI-based trading bot for Binance USDT-M Futures (Testnet) built as a hiring/task project. This repository demonstrates placing market and limit orders, an OCO helper, input validation, structured logging, and a dry-run simulation mode for safe testing.

Author: Harsh Murjani

## Features
- Place Market Orders (USDT-M Futures)
- Place Limit Orders (USDT-M Futures) with validation (price/tick, quantity/step)
- Stop-Limit Orders (trigger a limit order when a stop price is hit)
- OCO (One-Cancels-the-Other): entry (MARKET or optional LIMIT) → TP (LIMIT) + SL (STOP_MARKET) with background monitoring
- TWAP (Time-Weighted Average Price) strategy: split a large order into smaller chunks over time
- Grid trading strategy: place a grid of LIMIT buy/sell orders across a price range
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
│       ├── oco.py       # OCO helper (entry + TP + SL monitoring)
│       ├── stop_limit.py# Stop-Limit order helper
│       ├── twap.py      # TWAP strategy
│       └── grid.py      # Grid trading strategy
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

- stop-limit <symbol> <buy|sell> <quantity> <price> <stop_price> [--time-in-force]
	- Place a stop-limit order (trigger a limit order when stop price is hit)
	- Example: `python3 main.py stop-limit BTCUSDT buy 0.001 35100 35000`

- oco <symbol> <buy|sell> <quantity> <tp_price> <sl_price> [entry_price]
	- Place an OCO flow. If `entry_price` is provided the bot places a LIMIT entry and waits to fill; otherwise a MARKET entry is executed immediately.
	- Example (market entry): `python3 main.py oco BTCUSDT buy 0.001 110500 108000`
	- Example (limit entry): `python3 main.py oco BTCUSDT buy 0.001 110500 108000 109000`

- twap <symbol> <buy|sell> <total_quantity> <num_chunks> <duration_minutes> [--use-limit --limit-price]
	- Execute a TWAP strategy splitting `total_quantity` into `num_chunks` spread over `duration_minutes`.
	- Example: `python3 main.py twap BTCUSDT buy 0.003 3 10`

- grid <symbol> <upper_price> <lower_price> <num_grids> <quantity_per_grid>
	- Place a grid of LIMIT buy/sell orders between `lower_price` and `upper_price`.
	- Example: `python3 main.py grid BTCUSDT 110500 108500 3 0.01`

Dry-run (simulate without API calls):
```bash
python3 main.py --dry-run market BTCUSDT buy 0.001
```

## How validation works
- Symbol validity is checked against exchange info from the client
- Quantity is validated/rounded to the symbol's LOT_SIZE step
- Price is validated/rounded to the symbol's PRICE_FILTER tickSize

If validation fails, the CLI prints a helpful error and logs details to `bot.log`.

Note: Some exchange-side constraints (for example MIN_NOTIONAL / minimum order notional) are enforced by the exchange and may still return API errors even if local validation passes. The bot validates PRICE_FILTER and LOT_SIZE locally; you can improve it by validating MIN_NOTIONAL (price * qty) before sending orders.

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

5. Place a stop-limit order (testnet):
```bash
python3 main.py stop-limit BTCUSDT buy 0.001 35100 35000
```

6. Place an OCO order (testnet):
```bash
python3 main.py oco BTCUSDT buy 0.001 110500 108000
```

7. Run TWAP (testnet):
```bash
python3 main.py twap BTCUSDT sell 0.003 3 1
```

8. Run Grid (testnet) — ensure quantity & notional meet exchange minimums:
```bash
python3 main.py grid BTCUSDT 110500 108500 3 0.01
```

## Notes & Limitations
- This project is intentionally small and focused for a hiring task. It is not production-ready.
- No wallet/secret management beyond `.env` — keep secrets safe.
- Risk controls, position sizing, order lifecycle reconciliation, and concurrency protections are out of scope for this task but are natural next steps.

## Next steps (recommended)
- Add unit tests for validation logic (quantity/price step rounding)
- Add better reconciliation and order state persistence (DB or file)
- Improve min-notional validation to avoid exchange rejections

Author: Harsh Murjani
