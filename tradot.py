import ccxt
import pandas as pd
import ta
import time
import os
import logging
from dotenv import load_dotenv

log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, f"logs.log")
logging.basicConfig(filename=log_file, level=logging.INFO, 
                   format='%(asctime)s - %(message)s', datefmt='%d.%m %H:%M')

load_dotenv()
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')

exchange = ccxt.binance({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,  # Avoids hitting API limits
})
exchange.set_sandbox_mode(True)  # Testnet mode - fake money

SYMBOL = 'BTC/USDT'
TIMEFRAME = '5m'  # 5-minute candles
POSITION_SIZE = 0.05  # ~$3,000 at $60,000 BTC
PROFIT_TARGET = 0.03  # 3% profit
STOP_LOSS = 0.01      # 1% loss
DAILY_LOSS_CAP = 100  # Stop after $100 loss/day

in_position = False
entry_price = 0.0
daily_loss = 0.0

def fetch_ohlcv():
    ohlcv = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=200)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    return df

def calculate_indicators(df):
    # df['fast_ma'] = ta.trend.sma_indicator(df['close'], window=10)  # 10-period MA
    # df['slow_ma'] = ta.trend.sma_indicator(df['close'], window=50)  # 50-period MA
    df['fast_ma'] = ta.trend.sma_indicator(df['close'], window=5)
    df['slow_ma'] = ta.trend.sma_indicator(df['close'], window=20)
    df['rsi'] = ta.momentum.rsi(df['close'], window=14)             # RSI
    return df

def is_high_volatility(df):
    recent = df['close'].iloc[-15:]  # Last 15 candles (~75 mins)
    change = abs(recent.iloc[-1] - recent.iloc[0]) / recent.iloc[0] * 100
    return change > 3  # Pause if >3% swing

def scalp_trade():
    global in_position, entry_price, daily_loss
    last_loss_time = 0  # Cooldown tracker

    logging.info("Starting Tradot(TRAding-bOT) on Testnet...")
    while True:
        try:
            df = fetch_ohlcv()
            df = calculate_indicators(df)
            latest = df.iloc[-1]  # Current candle
            prev = df.iloc[-2]    # Previous candle
            price = latest['close']

            logging.info(f"Price: ${price:.2f}, Fast MA: {latest['fast_ma']:.2f}, Slow MA: {latest['slow_ma']:.2f}, RSI: {latest['rsi']:.2f}")

            # Pause conditions
            if is_high_volatility(df):
                logging.info("\nHigh volatility (>3%), pausing for 15 mins...\n")
                time.sleep(900)  # 15 mins
                continue
            if daily_loss >= DAILY_LOSS_CAP:
                logging.info("\nDaily loss cap ($100) hit, stopping for 24 hours...\n")
                time.sleep(86400)  # 24 hours
                daily_loss = 0
                continue

            # Trading logic
            if not in_position:
                # Buy signal: Fast MA crosses above Slow MA, RSI not overbought
                if (prev['fast_ma'] < prev['slow_ma'] and 
                    latest['fast_ma'] > latest['slow_ma'] and 
                    latest['rsi'] < 70 and 
                    time.time() - last_loss_time > 900):  # 15-min cooldown
                    order = exchange.create_market_buy_order(SYMBOL, POSITION_SIZE)
                    entry_price = price
                    in_position = True
                    logging.info(f"\nBought {POSITION_SIZE} BTC @ ${entry_price:.2f}\n")
            elif in_position:
                profit = (price - entry_price) / entry_price
                loss = (entry_price - price) / entry_price
                # Sell: Hit profit, stop-loss, or trend reverses
                if (profit >= PROFIT_TARGET or 
                    loss >= STOP_LOSS or 
                    latest['fast_ma'] < latest['slow_ma']):
                    order = exchange.create_market_sell_order(SYMBOL, POSITION_SIZE)
                    in_position = False
                    pl = (price - entry_price) * POSITION_SIZE  # Profit/loss in $
                    daily_loss += max(0, -pl)  # Track losses only
                    logging.info(f"\nSold {POSITION_SIZE} BTC @ ${price:.2f}, P/L: ${pl:.2f}\n")
                    if pl < 0:
                        last_loss_time = time.time()  # Start cooldown

            time.sleep(60)  # Check every minute

        except Exception as e:
            logging.info(f"Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    scalp_trade()
