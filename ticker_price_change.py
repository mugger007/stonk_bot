import yfinance as yf
import numpy as np
from typing import Optional, Tuple, List

def calculate_price_change(
    ticker: str,
    lookback: Optional[str] = "2d"
) -> Tuple[float, List]:
    # lookback (str, optional): price change period to evaluate on; defaults to "2d"

    stock = yf.Ticker(ticker)
    hist = stock.history(period = lookback).Close.values.tolist()
    if len(hist) != int(lookback[0]):
        lookback = f"{int(lookback[0]) + 1}d"
        hist = stock.history(period = lookback).Close.values.tolist()

    if not hist:
        return f"Could not find history for ticker {ticker}", None
    pct_chng = ((hist[-1] - hist[0]) / hist[0]) * 100

    return np.round(pct_chng, 2), hist
