import yfinance as yf
from typing import Optional

def last_quote(
    ticker: str,
    lookback: Optional[str] = "2d"):

    stock = yf.Ticker(ticker)
    hist = stock.history(period = lookback).Close.values.tolist()
    quote = hist[-1]

    return round(quote, 2)
