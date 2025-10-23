#!/usr/bin/env python3

import time
from typing import Dict, Any, List, Optional
from decimal import Decimal
from src.common import BasicBot, logger
from src.market_order import MarketOrder
from src.limit_order import LimitOrder
from binance.exceptions import BinanceAPIException
import threading

class TWAPStrategy:
    def __init__(self, bot: BasicBot):
        """Initialize TWAP strategy handler."""
        self.bot = bot
        self.market_order = MarketOrder(bot)
        self.limit_order = LimitOrder(bot)
        self._stop_event = threading.Event()
        
    def _validate_twap_params(self, total_quantity: float, num_chunks: int,
                            duration_minutes: float) -> None:
        """Validate TWAP strategy parameters."""
        if total_quantity <= 0:
            raise ValueError("Total quantity must be positive")
        if num_chunks < 2:
            raise ValueError("Number of chunks must be at least 2")
        if duration_minutes <= 0:
            raise ValueError("Duration must be positive")
            
    def _calculate_chunk_size(self, total_quantity: float, num_chunks: int,
                            symbol_info: Dict[str, Any]) -> float:
        """Calculate and validate individual chunk size."""
        chunk_size = total_quantity / num_chunks
        
        for filter in symbol_info['filters']:
            if filter['filterType'] == 'LOT_SIZE':
                min_qty = float(filter['minQty'])
                step_size = float(filter['stepSize'])
                
                if chunk_size < min_qty:
                    raise ValueError(
                        f"Chunk size {chunk_size} below minimum {min_qty}. "
                        "Try fewer chunks or larger total quantity."
                    )
                
                chunk_size = self.bot.round_step_size(chunk_size, step_size)
                
        return chunk_size

    def execute_twap(self, symbol: str, side: str, total_quantity: float,
                    num_chunks: int, duration_minutes: float,
                    use_limit_orders: bool = False, limit_price: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Execute a TWAP strategy by splitting a large order into smaller chunks.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: Order side ('BUY' or 'SELL')
            total_quantity: Total quantity to trade
            num_chunks: Number of chunks to split the order into
            duration_minutes: Total duration to spread the orders over
            use_limit_orders: If True, use limit orders instead of market orders
            limit_price: Required if use_limit_orders is True
            
        Returns:
            List of order responses from Binance
        """
        try:
            self._stop_event.clear()
            
            self._validate_twap_params(total_quantity, num_chunks, duration_minutes)
            symbol = symbol.upper()
            side = self.bot.format_side(side)
            
            if use_limit_orders and limit_price is None:
                raise ValueError("limit_price is required when use_limit_orders=True")
            
            if not self.bot.validate_symbol(symbol):
                raise ValueError(f"Invalid symbol: {symbol}")
                
            symbol_info = self.bot.get_symbol_info(symbol)
            if not symbol_info:
                raise ValueError(f"Could not get symbol info for {symbol}")
            
            chunk_size = self._calculate_chunk_size(total_quantity, num_chunks, symbol_info)
            interval_seconds = (duration_minutes * 60) / num_chunks
            
            orders = []
            remaining_chunks = num_chunks
            
            logger.info(
                f"Starting TWAP execution: {symbol} {side} {total_quantity} "
                f"in {num_chunks} chunks over {duration_minutes} minutes"
            )
            
            while remaining_chunks > 0 and not self._stop_event.is_set():
                chunk_start = time.time()
                
                try:
                    if use_limit_orders:
                        order = self.limit_order.place_order(
                            symbol=symbol,
                            side=side,
                            quantity=chunk_size,
                            price=limit_price,
                            time_in_force='GTC'
                        )
                    else:
                        order = self.market_order.place_order(
                            symbol=symbol,
                            side=side,
                            quantity=chunk_size
                        )
                    
                    orders.append(order)
                    logger.info(f"TWAP chunk {num_chunks - remaining_chunks + 1} executed: {order}")
                    
                except Exception as e:
                    logger.error(f"Error executing TWAP chunk: {str(e)}")
                    raise
                
                remaining_chunks -= 1
                
                if remaining_chunks > 0:
                    elapsed = time.time() - chunk_start
                    sleep_time = max(0, interval_seconds - elapsed)
                    time.sleep(sleep_time)
            
            if self._stop_event.is_set():
                logger.info("TWAP execution stopped by user")
            else:
                logger.info("TWAP execution completed successfully")
            
            return orders
            
        except Exception as e:
            logger.error(f"TWAP execution failed: {str(e)}")
            raise
            
    def stop(self):
        """Stop the TWAP execution (can be called from another thread)."""
        self._stop_event.set()
