#!/usr/bin/env python3

import time
import threading
from typing import Dict, Any, List, Optional
from decimal import Decimal
from src.common import BasicBot, logger
from src.limit_order import LimitOrder
from binance.exceptions import BinanceAPIException

class GridStrategy:
    def __init__(self, bot: BasicBot):
        """Initialize Grid Trading strategy handler."""
        self.bot = bot
        self.limit_order = LimitOrder(bot)
        self._stop_event = threading.Event()
        self._active_orders: Dict[int, Dict[str, Any]] = {}
        
    def _validate_grid_params(self, upper_price: float, lower_price: float,
                          num_grids: int, quantity_per_grid: float) -> None:
        """Validate grid strategy parameters."""
        if upper_price <= lower_price:
            raise ValueError("Upper price must be greater than lower price")
        if num_grids < 2:
            raise ValueError("Number of grids must be at least 2")
        if quantity_per_grid <= 0:
            raise ValueError("Quantity per grid must be positive")
            
    def _calculate_grid_levels(self, upper_price: float, lower_price: float,
                           num_grids: int, symbol_info: Dict[str, Any]) -> List[float]:
        """Calculate price levels for the grid."""
        price_step = (upper_price - lower_price) / (num_grids - 1)
        
        tick_size = None
        for filter in symbol_info['filters']:
            if filter['filterType'] == 'PRICE_FILTER':
                tick_size = float(filter['tickSize'])
                break
                
        if not tick_size:
            raise ValueError("Could not determine price tick size")
            
        levels = []
        for i in range(num_grids):
            price = lower_price + (i * price_step)
            price = self.bot.round_step_size(price, tick_size)
            levels.append(price)
            
        return levels

    def _validate_quantity(self, symbol_info: Dict[str, Any],
                       quantity_per_grid: float) -> float:
        """Validate grid order quantity."""
        for filter in symbol_info['filters']:
            if filter['filterType'] == 'LOT_SIZE':
                min_qty = float(filter['minQty'])
                max_qty = float(filter['maxQty'])
                step_size = float(filter['stepSize'])
                
                if quantity_per_grid < min_qty:
                    raise ValueError(f"Quantity {quantity_per_grid} below minimum {min_qty}")
                if quantity_per_grid > max_qty:
                    raise ValueError(f"Quantity {quantity_per_grid} above maximum {max_qty}")
                
                quantity_per_grid = self.bot.round_step_size(quantity_per_grid, step_size)
                
        return quantity_per_grid

    def execute_grid(self, symbol: str, upper_price: float, lower_price: float,
                    num_grids: int, quantity_per_grid: float) -> List[Dict[str, Any]]:
        """
        Execute a grid trading strategy by placing orders at calculated price levels.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            upper_price: Highest price in the grid
            lower_price: Lowest price in the grid
            num_grids: Number of price levels in the grid
            quantity_per_grid: Order quantity at each grid level
            
        Returns:
            List of order responses from Binance
        """
        try:
            self._stop_event.clear()
            self._active_orders.clear()
            
            self._validate_grid_params(upper_price, lower_price, num_grids, quantity_per_grid)
            symbol = symbol.upper()
            
            if not self.bot.validate_symbol(symbol):
                raise ValueError(f"Invalid symbol: {symbol}")
                
            symbol_info = self.bot.get_symbol_info(symbol)
            if not symbol_info:
                raise ValueError(f"Could not get symbol info for {symbol}")
            
            price_levels = self._calculate_grid_levels(upper_price, lower_price, num_grids, symbol_info)
            quantity_per_grid = self._validate_quantity(symbol_info, quantity_per_grid)
            
            logger.info(
                f"Starting grid strategy: {symbol} with {num_grids} levels "
                f"from {lower_price} to {upper_price}"
            )
            
            orders = []
            for i in range(len(price_levels) - 1):
                try:
                    buy_order = self.limit_order.place_order(
                        symbol=symbol,
                        side='BUY',
                        quantity=quantity_per_grid,
                        price=price_levels[i],
                        time_in_force='GTC'
                    )
                    orders.append(buy_order)
                    self._active_orders[buy_order['orderId']] = buy_order
                    
                    sell_order = self.limit_order.place_order(
                        symbol=symbol,
                        side='SELL',
                        quantity=quantity_per_grid,
                        price=price_levels[i + 1],
                        time_in_force='GTC'
                    )
                    orders.append(sell_order)
                    self._active_orders[sell_order['orderId']] = sell_order
                    
                except Exception as e:
                    logger.error(f"Error placing grid orders: {str(e)}")
                    self.stop()
                    raise
            
            monitor_thread = threading.Thread(
                target=self._monitor_and_replace_orders,
                args=(symbol,)
            )
            monitor_thread.start()
            
            return orders
            
        except Exception as e:
            logger.error(f"Grid strategy initialization failed: {str(e)}")
            raise
            
    def _monitor_and_replace_orders(self, symbol: str):
        """Monitor filled orders and replace them to maintain the grid."""
        while not self._stop_event.is_set():
            try:
                for order_id, order in list(self._active_orders.items()):
                    status = self.bot.client.futures_get_order(
                        symbol=symbol,
                        orderId=order_id
                    )
                    
                    if status['status'] == 'FILLED':
                        logger.info(f"Grid order filled: {status}")
                        
                        del self._active_orders[order_id]
                        
                        new_side = 'SELL' if order['side'] == 'BUY' else 'BUY'
                        new_price = float(order['price']) * (1.01 if new_side == 'SELL' else 0.99)
                        
                        try:
                            new_order = self.limit_order.place_order(
                                symbol=symbol,
                                side=new_side,
                                quantity=float(order['origQty']),
                                price=new_price,
                                time_in_force='GTC'
                            )
                            self._active_orders[new_order['orderId']] = new_order
                            logger.info(f"Placed replacement grid order: {new_order}")
                            
                        except Exception as e:
                            logger.error(f"Error placing replacement order: {str(e)}")
                
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in grid monitor thread: {str(e)}")
                if not self._stop_event.is_set():
                    time.sleep(10)
                    
    def stop(self):
        """Stop the grid strategy and cancel all active orders."""
        self._stop_event.set()
        
        for order_id, order in self._active_orders.items():
            try:
                self.bot.client.futures_cancel_order(
                    symbol=order['symbol'],
                    orderId=order_id
                )
                logger.info(f"Cancelled grid order: {order_id}")
            except Exception as e:
                logger.error(f"Error cancelling order {order_id}: {str(e)}")
        
        self._active_orders.clear()