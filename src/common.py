# shared utilities for validation, client creation, and logging
import os
import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal, ROUND_DOWN
from dotenv import load_dotenv
from binance.client import Client
from binance.exceptions import BinanceAPIException
import time
from typing import Union

# Configure logging
LOG_FILE = os.path.join(os.getcwd(), 'bot.log')
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('binance_bot')

class BasicBot:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        """Initialize the trading bot.

        Supports dry-run mode by setting `dry_run=True` when creating the bot.
        """
        self.dry_run = False
        # real client will be created on demand if not in dry-run
        self.client: Union[Client, DummyClient, None] = None
        if api_key and api_secret:
            self._api_key = api_key
            self._api_secret = api_secret
        else:
            self._api_key = None
            self._api_secret = None
        self.testnet = testnet
        logger.info("BasicBot created (client not yet initialized)")
        # Note: credential check happens when client is initialized (or skipped in dry-run)

    def init_client(self, dry_run: bool = False):
        """Initialize the real or dummy client based on dry_run flag."""
        self.dry_run = dry_run
        if dry_run:
            # lightweight DummyClient for simulation
            self.client = DummyClient()
            logger.info("Initialized DummyClient for dry-run mode")
            return
        # create real client with testnet configuration
        self.client = Client(self._api_key, self._api_secret)
        if self.testnet:
            # Configure for demo.binance.com unified testnet
            self.client.API_URL = 'https://testnet.binance.vision/api'
            self.client.FUTURES_API_URL = 'https://testnet.binance.vision/fapi'
            self.client.FUTURES_URL = 'https://testnet.binance.vision'
            # Enable testnet mode
            self.client.tld = 'vision'  # Use testnet domain
            self.client.testnet = True
        logger.info("Real Binance client initialized")
        # quick permission/connectivity check
        try:
            self.client.futures_account_balance()
        except Exception as e:
            logger.error(f"API credential/permission check failed: {e}")
            raise

    # --- Helpers that delegate to the underlying client ---
    def get_quantity_precision(self, symbol_info: Dict[str, Any]) -> int:
        return int(symbol_info.get('quantityPrecision', 0))

    def get_price_precision(self, symbol_info: Dict[str, Any]) -> int:
        return int(symbol_info.get('pricePrecision', 0))

    def round_step_size(self, quantity: float, step_size: float) -> float:
        return float(Decimal(str(quantity)).quantize(Decimal(str(step_size)), rounding=ROUND_DOWN))

    def validate_symbol(self, symbol: str) -> bool:
        try:
            info = self.client.futures_exchange_info()
            symbols = [s['symbol'] for s in info['symbols']]
            return symbol.upper() in symbols
        except Exception as e:
            logger.error(f'validate_symbol exception: {e}')
            return False

    def format_side(self, side: str) -> str:
        s = side.lower()
        if s not in ('buy', 'sell'):
            raise ValueError('side must be buy or sell')
        return 'BUY' if s == 'buy' else 'SELL'

    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        try:
            info = self.client.futures_exchange_info()
            for item in info['symbols']:
                if item['symbol'] == symbol.upper():
                    return item
            return None
        except Exception as e:
            logger.error(f'Get symbol info error: {e}')
            return None

    def get_account_balance(self) -> List[Dict[str, Any]]:
        try:
            return self.client.futures_account_balance()
        except Exception as e:
            logger.error(f'Get account balance error: {e}')
            return []


class DummyClient:
    """A very small fake client that mimics the futures methods used by the bot.
    Returns deterministic, safe responses for testing the CLI without network calls.
    """
    def __init__(self):
        self._order_id = 100000

    def futures_account_balance(self):
        return [{"asset": "USDT", "balance": "1000.00"}]

    def futures_exchange_info(self):
        # minimal exchange info with BTCUSDT sample symbol and basic filters
        return {
            'symbols': [
                {
                    'symbol': 'BTCUSDT',
                    'pricePrecision': 2,
                    'quantityPrecision': 3,
                    'filters': [
                        {'filterType': 'PRICE_FILTER', 'minPrice': '0.01', 'maxPrice': '1000000', 'tickSize': '0.01'},
                        {'filterType': 'LOT_SIZE', 'minQty': '0.0001', 'maxQty': '1000', 'stepSize': '0.0001'}
                    ]
                }
            ]
        }

    def futures_create_order(self, **kwargs):
        # simulate an order creation
        self._order_id += 1
        order = {
            'orderId': self._order_id,
            'symbol': kwargs.get('symbol'),
            'side': kwargs.get('side'),
            'type': kwargs.get('type'),
            'origQty': str(kwargs.get('quantity')),
            'price': kwargs.get('price', ''),
            'status': 'NEW'
        }
        return order

    def futures_get_order(self, **kwargs):
        return {'orderId': kwargs.get('orderId'), 'status': 'FILLED'}

    def futures_cancel_order(self, **kwargs):
        return {'orderId': kwargs.get('orderId'), 'status': 'CANCELED'}
        
    
