#!/usr/bin/env python3

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import argparse
from src.common import BasicBot, logger
from src.market_order import MarketOrder
from src.limit_order import LimitOrder
from src.advance.oco import OCOOrder
from src.advance.stop_limit import StopLimitOrder
from src.advance.twap import TWAPStrategy
from src.advance.grid import GridStrategy

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
    load_dotenv()
    
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        print("❌ API credentials not found! Please add them to your .env file:")
        print("BINANCE_API_KEY=your_api_key")
        print("BINANCE_API_SECRET=your_api_secret")
        return
    
    try:
        bot = BasicBot(api_key, api_secret, testnet=True)
    except Exception as e:
        logger.error(f"Failed to create bot: {str(e)}")
        print(f"❌ Initialization failed: {str(e)}")
        return

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--dry-run', action='store_true', help='Run in simulation mode without sending API requests')
    known_args, remaining_argv = parser.parse_known_args()
    dry_run_flag = known_args.dry_run

    try:
        bot.init_client(dry_run=dry_run_flag)
    except Exception as e:
        logger.error(f"Failed to initialize client: {e}")
        print(f"❌ Initialization failed: {e}")
        return

    try:
        market_order = MarketOrder(bot)
        limit_order = LimitOrder(bot)
        oco_order = OCOOrder(bot)
        stop_limit_order = StopLimitOrder(bot)
        twap_strategy = TWAPStrategy(bot)
        grid_strategy = GridStrategy(bot)
    except Exception as e:
        logger.error(f"Failed to initialize order handlers: {str(e)}")
        print(f"❌ Initialization failed: {str(e)}")
        return

    parser = argparse.ArgumentParser(description='Binance Futures Trading Bot')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    balance_parser = subparsers.add_parser('balance', help='Show account balance')
    
    market_parser = subparsers.add_parser('market', help='Place a market order')
    market_parser.add_argument('symbol', help='Trading pair symbol (e.g., BTCUSDT)')
    market_parser.add_argument('side', choices=['buy', 'sell'], help='Order side')
    market_parser.add_argument('quantity', type=float, help='Order quantity')
    
    limit_parser = subparsers.add_parser('limit', help='Place a limit order')
    limit_parser.add_argument('symbol', help='Trading pair symbol (e.g., BTCUSDT)')
    limit_parser.add_argument('side', choices=['buy', 'sell'], help='Order side')
    limit_parser.add_argument('quantity', type=float, help='Order quantity')
    limit_parser.add_argument('price', type=float, help='Limit price')
    limit_parser.add_argument('--time-in-force', choices=['GTC', 'IOC', 'FOK'], 
                             default='GTC', help='Time in force')
    
    oco_parser = subparsers.add_parser('oco', help='Place an OCO order')
    oco_parser.add_argument('symbol', help='Trading pair symbol (e.g., BTCUSDT)')
    oco_parser.add_argument('side', choices=['buy', 'sell'], help='Order side')
    oco_parser.add_argument('quantity', type=float, help='Order quantity')
    oco_parser.add_argument('tp_price', type=float, help='Take-profit limit price')
    oco_parser.add_argument('sl_price', type=float, help='Stop-loss trigger price')
    oco_parser.add_argument('entry_price', nargs='?', type=float, default=None,
                            help='Optional entry price to place a LIMIT entry order before TP/SL')
    
    stop_limit_parser = subparsers.add_parser('stop-limit', help='Place a stop-limit order')
    stop_limit_parser.add_argument('symbol', help='Trading pair symbol (e.g., BTCUSDT)')
    stop_limit_parser.add_argument('side', choices=['buy', 'sell'], help='Order side')
    stop_limit_parser.add_argument('quantity', type=float, help='Order quantity')
    stop_limit_parser.add_argument('price', type=float, help='Limit price')
    stop_limit_parser.add_argument('stop_price', type=float, help='Stop trigger price')
    stop_limit_parser.add_argument('--time-in-force', choices=['GTC', 'IOC', 'FOK'],
                                 default='GTC', help='Time in force')
    
    twap_parser = subparsers.add_parser('twap', help='Execute TWAP strategy')
    twap_parser.add_argument('symbol', help='Trading pair symbol (e.g., BTCUSDT)')
    twap_parser.add_argument('side', choices=['buy', 'sell'], help='Order side')
    twap_parser.add_argument('total_quantity', type=float, help='Total quantity to trade')
    twap_parser.add_argument('num_chunks', type=int, help='Number of chunks to split the order')
    twap_parser.add_argument('duration_minutes', type=float, help='Duration in minutes')
    twap_parser.add_argument('--use-limit', action='store_true', help='Use limit orders instead of market')
    twap_parser.add_argument('--limit-price', type=float, help='Limit price (required if use-limit is set)')
    
    grid_parser = subparsers.add_parser('grid', help='Execute grid trading strategy')
    grid_parser.add_argument('symbol', help='Trading pair symbol (e.g., BTCUSDT)')
    grid_parser.add_argument('upper_price', type=float, help='Upper price boundary')
    grid_parser.add_argument('lower_price', type=float, help='Lower price boundary')
    grid_parser.add_argument('num_grids', type=int, help='Number of grid levels')
    grid_parser.add_argument('quantity_per_grid', type=float, help='Order quantity per grid level')
    
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
            if args.entry_price is not None:
                orders = oco_order.place_oco_order(
                    args.symbol, args.side, args.quantity,
                    args.tp_price, args.sl_price,
                    entry_type='LIMIT', entry_price=args.entry_price
                )
            else:
                orders = oco_order.place_oco_order(
                    args.symbol, args.side, args.quantity,
                    args.tp_price, args.sl_price
                )

            print("\nOCO Order Details:")
            print("-" * 40)
            for order_type, order in orders.items():
                print(f"\n{order_type.upper()}:")
                display_order_info(order)
                
        elif args.command == 'stop-limit':
            order = stop_limit_order.place_order(
                args.symbol, args.side, args.quantity,
                args.price, args.stop_price, args.time_in_force
            )
            display_order_info(order)
            
        elif args.command == 'twap':
            if args.use_limit and args.limit_price is None:
                print("❌ Error: --limit-price is required when using --use-limit")
                return
                
            orders = twap_strategy.execute_twap(
                args.symbol, args.side, args.total_quantity,
                args.num_chunks, args.duration_minutes,
                args.use_limit, args.limit_price
            )
            
            print("\nTWAP Execution Details:")
            print("-" * 40)
            for i, order in enumerate(orders, 1):
                print(f"\nChunk {i}:")
                display_order_info(order)
                
        elif args.command == 'grid':
            orders = grid_strategy.execute_grid(
                args.symbol, args.upper_price, args.lower_price,
                args.num_grids, args.quantity_per_grid
            )
            
            print("\nGrid Strategy Details:")
            print("-" * 40)
            print(f"Total Orders Placed: {len(orders)}")
            for i, order in enumerate(orders, 1):
                print(f"\nGrid Order {i}:")
                display_order_info(order)
                
        else:
            parser.print_help()
            
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
