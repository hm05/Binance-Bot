#!/usr/bin/env python3
"""
Limit Order implementation for Binance Futures.
Handles limit orders with proper validation and error handling.
"""
from typing import Dict, Any
from decimal import Decimal
from src.common import BasicBot, logger
from binance.enums import *
from binance.exceptions import BinanceAPIException

class LimitOrder:
    def __init__(self, bot: BasicBot):
        """Initialize LimitOrder handler."""
        self.bot = bot
        self.ORDER_TYPE_LIMIT = 'LIMIT'

    def _validate_quantity(self, symbol_info: Dict[str, Any], quantity: float) -> float:
        """
        Validate and format the order quantity according to symbol rules.
        
        Args:
            symbol_info: Symbol information from Binance
            quantity: Original quantity
            
        Returns:
            Formatted quantity that meets symbol requirements
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
            
        # Get symbol filters
        for filter in symbol_info['filters']:
            if filter['filterType'] == 'LOT_SIZE':
                min_qty = float(filter['minQty'])
                max_qty = float(filter['maxQty'])
                step_size = float(filter['stepSize'])
                
                if quantity < min_qty:
                    raise ValueError(f"Quantity {quantity} below minimum {min_qty}")
                if quantity > max_qty:
                    raise ValueError(f"Quantity {quantity} above maximum {max_qty}")
                
                # Round to valid step size
                quantity = self.bot.round_step_size(quantity, step_size)
                
        return quantity

    def _validate_price(self, symbol_info: Dict[str, Any], price: float) -> float:
        """
        Validate and format the order price according to symbol rules.
        
        Args:
            symbol_info: Symbol information from Binance
            price: Original price
            
        Returns:
            Formatted price that meets symbol requirements
        """
        if price <= 0:
            raise ValueError("Price must be positive")
            
        # Get symbol filters
        for filter in symbol_info['filters']:
            if filter['filterType'] == 'PRICE_FILTER':
                min_price = float(filter['minPrice'])
                max_price = float(filter['maxPrice'])
                tick_size = float(filter['tickSize'])
                
                if price < min_price:
                    raise ValueError(f"Price {price} below minimum {min_price}")
                if price > max_price:
                    raise ValueError(f"Price {price} above maximum {max_price}")
                
                # Round to valid tick size
                price = self.bot.round_step_size(price, tick_size)
                
        return price

    def place_order(self, symbol: str, side: str, quantity: float, 
                   price: float, time_in_force: str = 'GTC') -> Dict[str, Any]:
        """
        Place a limit order on Binance Futures.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: Order side ('BUY' or 'SELL')
            quantity: Order quantity
            price: Limit price
            time_in_force: Time in force policy ('GTC', 'IOC', or 'FOK')
            
        Returns:
            Dict containing order details from Binance
            
        Raises:
            ValueError: If inputs are invalid
            BinanceAPIException: If order placement fails
        """
        try:
            # Validate symbol and get trading rules
            symbol = symbol.upper()
            if not self.bot.validate_symbol(symbol):
                raise ValueError(f"Invalid symbol: {symbol}")
                
            symbol_info = self.bot.get_symbol_info(symbol)
            if not symbol_info:
                raise ValueError(f"Could not get symbol info for {symbol}")
            
            # Format and validate inputs
            side = self.bot.format_side(side)
            quantity = self._validate_quantity(symbol_info, quantity)
            price = self._validate_price(symbol_info, price)
            
            # Validate time in force
            time_in_force = time_in_force.upper()
            if time_in_force not in ['GTC', 'IOC', 'FOK']:
                raise ValueError("Time in force must be 'GTC', 'IOC', or 'FOK'")
            
            # Place the order
            order = self.bot.client.futures_create_order(
                symbol=symbol,
                side=side,
                type=self.ORDER_TYPE_LIMIT,
                timeInForce=time_in_force,
                quantity=quantity,
                price=str(price)  # Binance expects string for price
            )
            
            logger.info(f"Limit order placed successfully: {order}")
            return order
            
        except BinanceAPIException as e:
            logger.error(f"Binance API error placing limit order: {str(e)}")
            raise
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error placing limit order: {str(e)}")
            raise