3. Add `.env` and `bot.log` to `.gitignore`.
## Usage examples
Market order (buy 0.001 BTC):
```
python src/market_orders.py BTCUSDT buy 0.001
```
Limit order (sell 0.001 BTC at 60,000):
```
python src/limit_orders.py BTCUSDT sell 0.001 --price 60000
```
TWAP example (split 0.1 BTC into 5 slices over 60 seconds):
```
python src/advanced/twap.py BTCUSDT buy 0.1 --slices 5 --duration 60
```
OCO example (place take-profit and stop-loss):
```
python src/advanced/oco.py BTCUSDT buy 0.001 --tp_price 61000 --sl_price 58000
```

Notes
* Use Testnet while testing (TESTNET=true) to avoid risking real funds.
* Do not share your `.env` or API keys.
```
---

## `requirements.txt`

```
python-binance==1.0.16 python-dotenv requests
```
---
## `.gitignore`
```
.env bot.log pycache/ *.pyc
```
---
## `src/__init__.py`

```python
# package initializer for src