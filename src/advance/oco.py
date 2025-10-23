#!/usr/bin/env python3
"""
OCO (One-Cancels-the-Other) implementation for Binance Futures (simulated).
This places an entry order (market or limit), then places a take-profit limit
and a stop-loss STOP_MARKET order, monitoring them and cancelling the loser.

This module uses the project's BasicBot class and avoids importing enum
constants that may differ between python-binance versions; it uses string
constants instead.
"""
import time
from typing import Dict, Any, Optional, Tuple
from src.common import BasicBot, logger
from binance.exceptions import BinanceAPIException

POLL_INTERVAL = 2.0

class OCOOrder:
    def __init__(self, bot: BasicBot):
        self.bot = bot
        self._monitoring = False
        # Use string literals to avoid enum import issues across versions
        self.ORDER_TYPE_MARKET = 'MARKET'
        self.ORDER_TYPE_LIMIT = 'LIMIT'
        self.ORDER_TYPE_STOP_MARKET = 'STOP_MARKET'
        self.TIME_IN_FORCE_GTC = 'GTC'

    def _place_entry_order(self, symbol: str, side: str, quantity: float,
                           entry_type: str = 'MARKET', entry_price: Optional[float] = None) -> Dict[str, Any]:
        try:
            params = {
                'symbol': symbol,
                'side': side,
                'type': entry_type,
                'quantity': quantity
            }
            if entry_type == self.ORDER_TYPE_LIMIT and entry_price is not None:
                params.update({
                    'timeInForce': self.TIME_IN_FORCE_GTC,
                    'price': str(entry_price)
                })

            order = self.bot.client.futures_create_order(**params)
            logger.info(f"Entry order placed: {order}")
            return order
        except BinanceAPIException as e:
            logger.error(f"Entry order failed: {e}")
            raise

    def _place_tp_sl_orders(self, symbol: str, side: str, quantity: float,
                             tp_price: float, sl_price: float) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        exit_side = 'SELL' if side == 'BUY' else 'BUY'

        tp_order = self.bot.client.futures_create_order(
            symbol=symbol,
            side=exit_side,
            type=self.ORDER_TYPE_LIMIT,
            timeInForce=self.TIME_IN_FORCE_GTC,
            quantity=quantity,
            price=str(tp_price),
            reduceOnly=True
        )

        sl_order = self.bot.client.futures_create_order(
            symbol=symbol,
            side=exit_side,
            type=self.ORDER_TYPE_STOP_MARKET,
            stopPrice=str(sl_price),
            quantity=quantity,
            reduceOnly=True
        )

        logger.info(f"TP order: {tp_order}")
        logger.info(f"SL order: {sl_order}")
        return tp_order, sl_order

    def _monitor_orders(self, symbol: str, tp_order_id: int, sl_order_id: int):
        self._monitoring = True
        try:
            while self._monitoring:
                tp_status = self.bot.client.futures_get_order(symbol=symbol, orderId=tp_order_id)
                sl_status = self.bot.client.futures_get_order(symbol=symbol, orderId=sl_order_id)

                if tp_status.get('status') == 'FILLED':
                    self.bot.client.futures_cancel_order(symbol=symbol, orderId=sl_order_id)
                    logger.info('TP filled; cancelled SL')
                    break
                if sl_status.get('status') == 'FILLED':
                    self.bot.client.futures_cancel_order(symbol=symbol, orderId=tp_order_id)
                    logger.info('SL filled; cancelled TP')
                    break

                time.sleep(POLL_INTERVAL)
        except Exception as e:
            logger.error(f"Error monitoring OCO orders: {e}")
        finally:
            self._monitoring = False

    def place_oco_order(self, symbol: str, side: str, quantity: float,
                        tp_price: float, sl_price: float,
                        entry_type: str = 'MARKET', entry_price: Optional[float] = None) -> Dict[str, Any]:
        symbol = symbol.upper()
        side = self.bot.format_side(side)

        if not self.bot.validate_symbol(symbol):
            raise ValueError(f"Invalid symbol: {symbol}")

        symbol_info = self.bot.get_symbol_info(symbol)
        if not symbol_info:
            raise ValueError(f"Could not retrieve symbol info for {symbol}")

        # place entry
        entry = self._place_entry_order(symbol, side, quantity, entry_type, entry_price)

        # if limit entry, wait until filled
        if entry_type == self.ORDER_TYPE_LIMIT:
            while True:
                st = self.bot.client.futures_get_order(symbol=symbol, orderId=entry['orderId'])
                if st.get('status') == 'FILLED':
                    break
                time.sleep(POLL_INTERVAL)

        tp_order, sl_order = self._place_tp_sl_orders(symbol, side, quantity, tp_price, sl_price)
        # monitor (blocking)
        self._monitor_orders(symbol, tp_order['orderId'], sl_order['orderId'])

        return {'entry': entry, 'tp': tp_order, 'sl': sl_order}