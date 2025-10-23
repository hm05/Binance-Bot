"""
Small script to verify Binance Futures Testnet API keys from .env
Prints the account balance on success or the raw error on failure.
"""
from dotenv import load_dotenv
import os
from binance.client import Client

load_dotenv()
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')

if not API_KEY or not API_SECRET:
    print('No API keys found in .env')
    raise SystemExit(1)

client = Client(API_KEY, API_SECRET)
<<<<<<< HEAD
# Ensure futures testnet base URL
client.API_URL = 'https://testnet.binancefuture.com/fapi/v1'
=======
# Configure for demo.binance.com unified testnet
client.API_URL = 'https://testnet.binance.vision/api'
client.FUTURES_API_URL = 'https://testnet.binance.vision/fapi'
client.FUTURES_URL = 'https://testnet.binance.vision'
client.tld = 'vision'  # Use testnet domain
client.testnet = True
>>>>>>> new

try:
    balances = client.futures_account_balance()
    print('Success: fetched futures account balance:')
    for b in balances:
        print(f"  {b['asset']}: {b.get('balance')}")
except Exception as e:
    err = repr(e)
    print('Error while verifying keys:')
    print(err)

    # Provide troubleshooting tips for the common -2015 error
    if '-2015' in err or 'Invalid API-key' in err:
        print('\nDetected Binance API error -2015 (Invalid API-key, IP, or permissions).')
        print('Common causes and fixes:')
        print('  1) You created API keys on Binance mainnet instead of the *Futures Testnet*.')
        print("     -> Go to the Binance Futures Testnet site and generate testnet API keys: https://testnet.binancefuture.com")
        print('  2) Your API key has IP restrictions enabled — remove them or add your current public IP. Testnet keys normally have no IP restriction.')
        print('  3) Your API key does not have trading/futures permissions enabled. Enable trading/futures permission in the API key settings.')
        print('  4) Make sure you pasted both API key and secret into your .env file and restarted the CLI/terminal session.')
        print('  5) Confirm the bot is configured for Futures Testnet (the script sets the testnet base URL).')
        print('\nIf you want, I can:')
        print(' - walk you step-by-step through creating testnet keys, or')
        print(' - check your .env file contents (locally) for formatting issues (I will not read your keys).')
    raise SystemExit(1)
