#!/usr/bin/env python3
"""
nifty50_intraday_movers.py

Fetches intraday (or last-session) open and current/last prices for NIFTY 50 stocks
and prints Top 5 Gainers and Top 5 Losers by % change from open -> current price.

Requirements:
  pip install yfinance pandas

Usage:
  python nifty50_intraday_movers.py
"""

import yfinance as yf
import pandas as pd
import sys
from datetime import datetime, timedelta

# Hardcoded NIFTY 50 symbols (as used on Yahoo Finance: append .NS)
NIFTY50 = [
"RELIANCE","HDFCBANK","BHARTIARTL","TCS","ICICIBANK","SBIN","BAJFINANCE","INFY",
"HINDUNILVR","LT","ITC","MARUTI","M&M","KOTAKBANK","HCLTECH","SUNPHARMA","AXISBANK",
"ULTRACEMCO","BAJAJFINSV","TITAN","NTPC","ONGC","ADANIPORTS","BEL","ADANIENT",
"TATACONSUM","APOLLOHOSP","DRREDDY","TATASTEEL","DIVISLAB","WIPRO","COALINDIA","BPCL",
"HEROMOTOCO","HDFC","JSWSTEEL","GRASIM","EICHERMOT","HINDALCO","UPL","BRITANNIA",
"TECHM","SBILIFE","ICICIPRULI","ONGC","NTPC","JSWSTEEL"  # note: some duplicates removed later
]

# Clean and deduplicate while keeping order
seen = set()
symbols = []
for s in NIFTY50:
    if s not in seen:
        seen.add(s)
        symbols.append(s + ".NS")

# For robustness, you can replace symbols with the exact current NIFTY50 list if needed.
# Using yfinance Tickers batch fetch
def fetch_data(symbols, interval='1m'):
    """
    Returns dict: symbol -> dict(open, price, pct_change)
    If market closed or intraday data unavailable, falls back to daily OHLC of most recent session.
    """
    results = {}
    tickers = yf.Tickers(' '.join(symbols))
    for sym in symbols:
        try:
            t = tickers.tickers.get(sym)
            if t is None:
                print(f"[WARN] ticker object not found for {sym}", file=sys.stderr)
                continue
            # Try intraday 1m for today
            now = datetime.now()
            hist = t.history(period="1d", interval=interval, actions=False)
            if hist.empty:
                # fallback to last 2 days daily bars
                dh = t.history(period="2d", interval="1d", actions=False)
                if dh.empty:
                    print(f"[WARN] No history for {sym}", file=sys.stderr)
                    continue
                last = dh.iloc[-1]
                open_price = float(last['Open'])
                current_price = float(last['Close'])
                source = "daily-close-fallback"
            else:
                # intraday available; take first open of the day and last available close/last price
                first = hist.iloc[0]
                last = hist.iloc[-1]
                open_price = float(first['Open'])
                current_price = float(last['Close']) if 'Close' in last else float(last['Close'])
                source = "intraday"
            pct = (current_price - open_price) / open_price * 100 if open_price != 0 else 0.0
            results[sym.replace(".NS","")] = {
                "symbol": sym.replace(".NS",""),
                "price": round(current_price,2),
                "open": round(open_price,2),
                "pct_change": round(pct,4),
                "source": source
            }
        except Exception as e:
            print(f"[ERROR] {sym}: {e}", file=sys.stderr)
    return results

def print_top_movers(results, topn=5):
    df = pd.DataFrame.from_dict(results, orient='index')
    if df.empty:
        print("No data fetched.")
        return
    df_sorted_pos = df.sort_values("pct_change", ascending=False).head(topn)
    df_sorted_neg = df.sort_values("pct_change", ascending=True).head(topn)
    pd.set_option('display.max_rows', None)
    print("\nTop {} Gainers:".format(topn))
    print(df_sorted_pos[['symbol','price','pct_change']].to_string(index=False, header=["SYMBOL","PRICE","% CHANGE"]))
    print("\nTop {} Losers:".format(topn))
    print(df_sorted_neg[['symbol','price','pct_change']].to_string(index=False, header=["SYMBOL","PRICE","% CHANGE"]))

if __name__ == "__main__":
    print("Fetching data for", len(symbols), "symbols...")
    results = fetch_data(symbols, interval='1m')
    print_top_movers(results, topn=5)
