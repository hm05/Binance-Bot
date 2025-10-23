#!/usr/bin/env python3

from typing import Dict, Any, Optional
from decimal import Decimal
from src.common import BasicBot, logger
from binance.exceptions import BinanceAPIException

class StopLimitOrder:
    def __init__(self, bot: BasicBot):
        """Initialize StopLimitOrder handler."""
        self.bot = bot
        self.ORDER_TYPE_STOP = 'STOP'
        self.ORDER_TYPE_STOP_LIMIT = 'STOP_LIMIT'

    def _validate_price(self, symbol_info: Dict[str, Any], price: float, stop_price: float) -> tuple[float, float]:
        """Validate both limit price and stop price."""
        if price <= 0 or stop_price <= 0:
            raise ValueError("Price and stop price must be positive")
            
        for filter in symbol_info['filters']:
            if filter['filterType'] == 'PRICE_FILTER':
                min_price = float(filter['minPrice'])
                max_price = float(filter['maxPrice'])
                tick_size = float(filter['tickSize'])
                
                if price < min_price or stop_price < min_price:
                    raise ValueError(f"Price {min(price, stop_price)} below minimum {min_price}")
                if price > max_price or stop_price > max_price:
                    raise ValueError(f"Price {max(price, stop_price)} above maximum {max_price}")
                
                price = self.bot.round_step_size(price, tick_size)
                stop_price = self.bot.round_step_size(stop_price, tick_size)
                
        return price, stop_price

    def _validate_quantity(self, symbol_info: Dict[str, Any], quantity: float) -> float:
        """Validate order quantity."""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
            
        for filter in symbol_info['filters']:
            if filter['filterType'] == 'LOT_SIZE':
                min_qty = float(filter['minQty'])
                max_qty = float(filter['maxQty'])
                step_size = float(filter['stepSize'])
                
                if quantity < min_qty:
                    raise ValueError(f"Quantity {quantity} below minimum {min_qty}")
                if quantity > max_qty:
                    raise ValueError(f"Quantity {quantity} above maximum {max_qty}")
                
                quantity = self.bot.round_step_size(quantity, step_size)
                
        return quantity

    def place_order(self, symbol: str, side: str, quantity: float, 
                   price: float, stop_price: float,
                   time_in_force: str = 'GTC') -> Dict[str, Any]:
        """
        Place a stop-limit order on Binance Futures.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: Order side ('BUY' or 'SELL')
            quantity: Order quantity
            price: Limit price for the order
            stop_price: Trigger price to activate the limit order
            time_in_force: Time in force policy ('GTC', 'IOC', or 'FOK')
            
        Returns:
            Dict containing order details from Binance
        """
        try:
            symbol = symbol.upper()
            if not self.bot.validate_symbol(symbol):
                raise ValueError(f"Invalid symbol: {symbol}")
                
            symbol_info = self.bot.get_symbol_info(symbol)
            if not symbol_info:
                raise ValueError(f"Could not get symbol info for {symbol}")
            
            side = self.bot.format_side(side)
            quantity = self._validate_quantity(symbol_info, quantity)
            price, stop_price = self._validate_price(symbol_info, price, stop_price)
            
            time_in_force = time_in_force.upper()
            if time_in_force not in ['GTC', 'IOC', 'FOK']:
                raise ValueError("Time in force must be 'GTC', 'IOC', or 'FOK'")
            
            order = self.bot.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='STOP',
                timeInForce=time_in_force,
                quantity=quantity,
                price=str(price),
                stopPrice=str(stop_price),
                workingType='MARK_PRICE'
            )
            
            logger.info(f"Stop-limit order placed successfully: {order}")
            return order
            
        except BinanceAPIException as e:
            logger.error(f"Binance API error placing stop-limit order: {str(e)}")
            raise
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error placing stop-limit order: {str(e)}")
            raise