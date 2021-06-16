import yfinance as yf

def valid_ticker(
    ticker: str):

    # Check if ticker is valid
    stock = yf.Ticker(ticker)
    stock = stock.info

    if 'symbol' not in stock.keys():
        return False
    else:
        return True
