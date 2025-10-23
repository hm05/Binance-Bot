#!/usr/bin/env python3
"""
Binance Futures Trading Bot
A command-line interface for placing various order types on Binance Futures testnet.
"""
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import argparse
from src.common import BasicBot, logger
from src.market_order import MarketOrder
from src.limit_order import LimitOrder
from src.advance.oco import OCOOrder

def display_balance(bot: BasicBot):
    """Display current account balance."""
    try:
        balances = bot.get_account_balance()
        print("\nAccount Balances:")
        print("-" * 40)
        for balance in balances:
            if float(balance['balance']) > 0:
                print(f"{balance['asset']}: {balance['balance']}")
        print("-" * 40)
    except Exception as e:
        logger.error(f"Error getting balance: {str(e)}")
        print("❌ Failed to get account balance")

def display_order_info(order: Dict[str, Any]):
    """Display order information in a formatted way."""
    print("\nOrder Details:")
    print("-" * 40)
    print(f"Order ID: {order['orderId']}")
    print(f"Symbol: {order['symbol']}")
    print(f"Side: {order['side']}")
    print(f"Type: {order['type']}")
    print(f"Quantity: {order['origQty']}")
    if 'price' in order:
        print(f"Price: {order['price']}")
    print("-" * 40)

def main():
    """Main entry point for the trading bot CLI."""
    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        print("❌ API credentials not found! Please add them to your .env file:")
        print("BINANCE_API_KEY=your_api_key")
        print("BINANCE_API_SECRET=your_api_secret")
        return
    
    # Initialize the bot
    try:
        bot = BasicBot(api_key, api_secret, testnet=True)
    except Exception as e:
        logger.error(f"Failed to create bot: {str(e)}")
        print(f"❌ Initialization failed: {str(e)}")
        return

    # Parse a global dry-run flag before subcommands
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--dry-run', action='store_true', help='Run in simulation mode without sending API requests')
    known_args, remaining_argv = parser.parse_known_args()
    dry_run_flag = known_args.dry_run

    # initialize client (real or dummy)
    try:
        bot.init_client(dry_run=dry_run_flag)
    except Exception as e:
        logger.error(f"Failed to initialize client: {e}")
        print(f"❌ Initialization failed: {e}")
        return

    # create order handlers using the initialized bot
    try:
        market_order = MarketOrder(bot)
        limit_order = LimitOrder(bot)
        oco_order = OCOOrder(bot)
    except Exception as e:
        logger.error(f"Failed to initialize order handlers: {str(e)}")
        print(f"❌ Initialization failed: {str(e)}")
        return

    # Set up argument parser with subcommands
    parser = argparse.ArgumentParser(description='Binance Futures Trading Bot')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Balance command
    balance_parser = subparsers.add_parser('balance', help='Show account balance')
    
    # Market order command
    market_parser = subparsers.add_parser('market', help='Place a market order')
    market_parser.add_argument('symbol', help='Trading pair symbol (e.g., BTCUSDT)')
    market_parser.add_argument('side', choices=['buy', 'sell'], help='Order side')
    market_parser.add_argument('quantity', type=float, help='Order quantity')
    
    # Limit order command
    limit_parser = subparsers.add_parser('limit', help='Place a limit order')
    limit_parser.add_argument('symbol', help='Trading pair symbol (e.g., BTCUSDT)')
    limit_parser.add_argument('side', choices=['buy', 'sell'], help='Order side')
    limit_parser.add_argument('quantity', type=float, help='Order quantity')
    limit_parser.add_argument('price', type=float, help='Limit price')
    limit_parser.add_argument('--time-in-force', choices=['GTC', 'IOC', 'FOK'], 
                             default='GTC', help='Time in force')
    
    # OCO order command
    oco_parser = subparsers.add_parser('oco', help='Place an OCO order')
    oco_parser.add_argument('symbol', help='Trading pair symbol (e.g., BTCUSDT)')
    oco_parser.add_argument('side', choices=['buy', 'sell'], help='Order side')
    oco_parser.add_argument('quantity', type=float, help='Order quantity')
    oco_parser.add_argument('price', type=float, help='Limit price')
    oco_parser.add_argument('stop_price', type=float, help='Stop price')
    oco_parser.add_argument('stop_limit_price', type=float, help='Stop limit price')
    
    # parse only the remaining args (we consumed --dry-run earlier)
    args = parser.parse_args(remaining_argv)
    
    try:
        if args.command == 'balance':
            display_balance(bot)
            return
            
        if args.command == 'market':
            order = market_order.place_order(
                args.symbol, args.side, args.quantity
            )
            display_order_info(order)
            
        elif args.command == 'limit':
            order = limit_order.place_order(
                args.symbol, args.side, args.quantity,
                args.price, args.time_in_force
            )
            display_order_info(order)
            
        elif args.command == 'oco':
            orders = oco_order.place_oco_order(
                args.symbol, args.side, args.quantity,
                args.price, args.stop_price, args.stop_limit_price
            )
            print("\nOCO Order Details:")
            print("-" * 40)
            for order_type, order in orders.items():
                print(f"\n{order_type.upper()}:")
                display_order_info(order)
        
        else:
            parser.print_help()
            
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
