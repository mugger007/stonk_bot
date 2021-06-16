import pandas_datareader as web
import datetime
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import yfinance as yf

def computeRSI(data, time_window):
    diff = data.diff(1).dropna()
    up_chg = 0 * diff
    down_chg = 0 * diff
    up_chg[diff > 0] = diff[ diff > 0 ]
    down_chg[diff < 0] = diff[ diff < 0 ]
    up_chg_avg = up_chg.ewm(com = time_window - 1 , min_periods = time_window).mean()
    down_chg_avg = down_chg.ewm(com = time_window - 1 , min_periods = time_window).mean()
    rs = abs(up_chg_avg/down_chg_avg)
    rsi = 100 - 100/(1+rs)

    return rsi

def rsi_notification(
    ticker: str):
    old_datetime = datetime.datetime.now() - datetime.timedelta(days = 365)
    rsi_db = web.get_data_yahoo(ticker,
        start = datetime.datetime(old_datetime.year, old_datetime.month, old_datetime.day),
        end = datetime.datetime(datetime.date.today().year, datetime.date.today().month, datetime.date.today().day))
    rsi_db = rsi_db[["Close"]]
    rsi_db.rename(columns = {"Close":"Price"}, inplace = True)
    rsi_db['RSI'] = computeRSI(rsi_db["Price"], 14)

    rsi_latest = rsi_db.iloc[-1,1].round(2)

    return rsi_latest

def intraday_rsi_notif(
    ticker: str):
    rsi_db = yf.download(
        tickers = ticker,
        period = "1d",
        interval = "5m",
        group_by = 'ticker',
        auto_adjust = True,
        prepost = True,
        threads = True,
        proxy = None
    )

    rsi_db = rsi_db[["Close"]]
    rsi_db.rename(columns = {"Close":"Price"}, inplace = True)

    rsi_db['RSI'] = computeRSI(rsi_db["Price"], 14)
    rsi_last = rsi_db.iloc[-1,1].round(2)

    return rsi_last

def macd_notification(
    ticker: str):
    old_datetime = datetime.datetime.now() - datetime.timedelta(days = 365)
    macd_db = web.get_data_yahoo(ticker,
        start = datetime.datetime(old_datetime.year, old_datetime.month, old_datetime.day),
        end = datetime.datetime(datetime.date.today().year, datetime.date.today().month, datetime.date.today().day))
    macd_db = macd_db[["Close"]]
    macd_db.rename(columns = {"Close":"Price"}, inplace = True)
    macd_db["12EMA"] = macd_db["Price"].ewm(span = 12).mean()
    macd_db["26EMA"] = macd_db["Price"].ewm(span = 26).mean()
    macd_db['MACD'] = macd_db["12EMA"] - macd_db["26EMA"]
    macd_db["signal"] = macd_db['MACD'].ewm(span = 9).mean()
    macd_db["hist"] = macd_db['MACD'] - macd_db["signal"]

    macd_diff_ystd = macd_db.iloc[-2,5].round(2)
    macd_diff_tdy = macd_db.iloc[-1,5].round(2)

    return macd_diff_ystd, macd_diff_tdy

def sma_notification(
    ticker: str):
    old_datetime = datetime.datetime.now() - datetime.timedelta(days = 365)
    sma_db = web.get_data_yahoo(ticker,
                              start = datetime.datetime(old_datetime.year, old_datetime.month, old_datetime.day),
                              end = datetime.datetime(datetime.date.today().year, datetime.date.today().month, datetime.date.today().day))
    sma_db = sma_db[["Close"]]
    sma_db.rename(columns = {"Close":"Price"}, inplace = True)
    sma_db["100MA"] = sma_db["Price"].rolling(window = 100).mean()
    sma_db["50MA"] = sma_db["Price"].rolling(window = 50).mean()
    sma_db["20MA"] = sma_db["Price"].rolling(window = 20).mean()

    sma_20_ystd = sma_db.iloc[-2,3].round(2)
    sma_20_tdy = sma_db.iloc[-1,3].round(2)
    sma_50_ystd = sma_db.iloc[-2,2].round(2)
    sma_50_tdy = sma_db.iloc[-1,2].round(2)
    sma_100_ystd = sma_db.iloc[-2,1].round(2)
    sma_100_tdy = sma_db.iloc[-1,1].round(2)
    sma_price_ystd = sma_db.iloc[-2,0].round(2)
    sma_price_tdy = sma_db.iloc[-1,0].round(2)

    return sma_20_ystd, sma_20_tdy, sma_50_ystd, sma_50_tdy, sma_100_ystd, sma_100_tdy, sma_price_ystd, sma_price_tdy

def ema_notification(
    ticker: str):
    old_datetime = datetime.datetime.now() - datetime.timedelta(days = 365)
    ema_db = web.get_data_yahoo(ticker,
                              start = datetime.datetime(old_datetime.year, old_datetime.month, old_datetime.day),
                              end = datetime.datetime(datetime.date.today().year, datetime.date.today().month, datetime.date.today().day))
    ema_db = ema_db[["Close"]]
    ema_db.rename(columns = {"Close":"Price"}, inplace = True)
    ema_db["100MA"] = ema_db["Price"].ewm(span = 100).mean()
    ema_db["50MA"] = ema_db["Price"].ewm(span = 50).mean()
    ema_db["20MA"] = ema_db["Price"].ewm(span = 20).mean()

    ema_20_ystd = ema_db.iloc[-2,3].round(2)
    ema_20_tdy = ema_db.iloc[-1,3].round(2)
    ema_50_ystd = ema_db.iloc[-2,2].round(2)
    ema_50_tdy = ema_db.iloc[-1,2].round(2)
    ema_100_ystd = ema_db.iloc[-2,1].round(2)
    ema_100_tdy = ema_db.iloc[-1,1].round(2)
    ema_price_ystd = ema_db.iloc[-2,0].round(2)
    ema_price_tdy = ema_db.iloc[-1,0].round(2)

    return ema_20_ystd, ema_20_tdy, ema_50_ystd, ema_50_tdy, ema_100_ystd, ema_100_tdy, ema_price_ystd, ema_price_tdy
