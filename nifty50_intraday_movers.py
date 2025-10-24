#!/usr/bin/env python3
"""
NIFTY 50 Intraday Movers - Clean Version
----------------------------------------
- Dynamically fetches NIFTY 50 symbols from NSE
- Removes invalid/dummy tickers
- Fetches intraday or daily prices from Yahoo Finance
- Prints Top 5 gainers and losers
"""

import pandas as pd
import yfinance as yf
import requests
import sys

# Step 1: Fetch live NIFTY 50 symbols
def fetch_nifty50_symbols():
    url = "https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv"
    headers = {"User-Agent": "Mozilla/5.0"}
    symbols = []
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        lines = response.text.strip().split("\n")
        for line in lines[1:]:
            parts = line.split(",")
            if len(parts) > 2:
                symbol = parts[2].strip()
                # Filter out invalid/dummy symbols
                if "DUMMY" not in symbol and symbol != "":
                    symbols.append(symbol + ".NS")
        return symbols
    except Exception as e:
        print(f"[ERROR] Failed to fetch NIFTY 50 list: {e}", file=sys.stderr)
        return []

# Step 2: Fetch intraday or daily data
def fetch_data(symbols, interval='1m'):
    results = {}
    tickers = yf.Tickers(' '.join(symbols))
    for sym in symbols:
        try:
            t = tickers.tickers.get(sym)
            hist = t.history(period="1d", interval=interval, actions=False)
            if hist.empty:
                # fallback to last daily data
                daily = t.history(period="2d", interval="1d", actions=False)
                if daily.empty:
                    continue
                last = daily.iloc[-1]
                open_price, current_price = float(last['Open']), float(last['Close'])
                source = "daily"
            else:
                first, last = hist.iloc[0], hist.iloc[-1]
                open_price, current_price = float(first['Open']), float(last['Close'])
                source = "intraday"

            pct = (current_price - open_price) / open_price * 100 if open_price else 0
            results[sym.replace(".NS","").strip()] = {
                "symbol": sym.replace(".NS","").strip(),
                "price": round(current_price, 2),
                "pct_change": round(pct, 2),
                "source": source
            }
        except Exception as e:
            print(f"[WARN] {sym}: {e}", file=sys.stderr)
    return results

# Step 3: Print Top Gainers & Losers
def print_top_movers(results, topn=5):
    df = pd.DataFrame(results).T
    if df.empty:
        print("No data available.")
        return
    df_pos = df.sort_values("pct_change", ascending=False).head(topn)
    df_neg = df.sort_values("pct_change", ascending=True).head(topn)

    print("\nTop 5 Gainers:")
    print(df_pos[["symbol", "price", "pct_change"]].to_string(index=False, header=["SYMBOL", "PRICE", "% CHANGE"]))

    print("\nTop 5 Losers:")
    print(df_neg[["symbol", "price", "pct_change"]].to_string(index=False, header=["SYMBOL", "PRICE", "% CHANGE"]))

# ---- Main ----
if __name__ == "__main__":
    print("Fetching live NIFTY 50 symbols...")
    nifty50_symbols = fetch_nifty50_symbols()
    print(f"Fetched {len(nifty50_symbols)} symbols.")

    print("Fetching intraday data...")
    results = fetch_data(nifty50_symbols)
    print_top_movers(results)
