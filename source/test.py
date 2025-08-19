import yfinance as yf
import pandas as pd
from datetime import date, datetime

# Map your tickers to Yahoo equivalents
tickers = {
    "NIFTY 50": "^NSEI",
    "FINNIFTY": "^CNXFIN",
    "BANKNIFTY": "^NSEBANK",
    "NIFTY NEXT 50": None,   # Not on Yahoo
    "MIDCAP NIFTY": None     # Not on Yahoo
}

today_str = pd.to_datetime(date.today()).strftime("%Y-%m-%d")
print("Current time :", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

for name, symbol in tickers.items():
    print(f"\n=== {name} ({symbol if symbol else 'N/A'}) ===")
    if symbol:
        # Fetch last 2 daily bars
        df = yf.download(symbol, period="2d", interval="1d", auto_adjust=True, prepost=False)
        
        if today_str in df.index.strftime("%Y-%m-%d"):
            print("✅ Today's OHLCV available")
            print(df.loc[df.index[-1]])
        else:
            # Fallback: build from intraday 5m bars
            intraday = yf.download(symbol, period="1d", interval="5m", auto_adjust=True, prepost=False)
            if not intraday.empty:
                daily = intraday.resample("1D").agg({
                    "Open": "first",
                    "High": "max",
                    "Low": "min",
                    "Close": "last",
                    "Volume": "sum"
                })
                print("⚡ Built today's OHLCV from intraday data")
                print(daily.tail(1))
            else:
                print("❌ No data found today")
    else:
        print("❌ Not available on Yahoo Finance. Use NSE API/ETFs instead.")
