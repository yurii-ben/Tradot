# Tradot (TRAding-bOT)

Tradot is a Python-based automated trading bot that connects to Binance's testnet (using fake money) to trade Bitcoin (BTC) against Tether (USDT). The bot performs technical analysis using moving averages and RSI to make buy and sell decisions. It implements basic risk management features, such as a profit target, stop loss, and a daily loss cap to protect against large losses.

## Features

- **Technical Indicators**: Uses 5-period and 20-period simple moving averages (SMA) and Relative Strength Index (RSI) to determine trading signals.
- **Risk Management**: Includes a profit target (3%), stop loss (1%), and daily loss cap ($100).
- **Sandbox Trading**: Trades on Binance's testnet to ensure safety during development and testing.
- **Logging**: Logs detailed trade and error information for monitoring and debugging.

## VMConfig

- **cat logging.log** - review file
- **tail -f logging.log** - live monitoring
- **ssh -i tradot-gcp @username@ip** - connect to VM from local
- **scp -i tradot-gcp tradot.zip @username@ip:~** - transfer file to VM. Run locally
- **unzip tradot.zip**
- **python3 tradot.py & disown** - launch on background
