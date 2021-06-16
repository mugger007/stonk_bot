import pandas_datareader as web
import datetime
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

# calculate RSI based on formula
def computeRSI(data, time_window):
    diff = data.diff(1).dropna() # diff in one field(one day)
    # preservers dimensions off diff values
    up_chg = 0 * diff
    down_chg = 0 * diff
    # up change is equal to the positive difference, otherwise equal to zero
    up_chg[diff > 0] = diff[ diff > 0 ]
    # down change is equal to negative deifference, otherwise equal to zero
    down_chg[diff < 0] = diff[ diff < 0 ]
    # check pandas documentation for ewm
    # https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.ewm.html
    # values are related to exponential decay
    # we set com = time_window-1 so we get decay alpha=1/time_window
    up_chg_avg = up_chg.ewm(com = time_window - 1 , min_periods = time_window).mean()
    down_chg_avg = down_chg.ewm(com = time_window - 1 , min_periods = time_window).mean()

    rs = abs(up_chg_avg/down_chg_avg)
    rsi = 100 - 100/(1+rs)
    return rsi

def last_year_rsi(
    ticker: str):
    old_datetime = datetime.datetime.now() - datetime.timedelta(days = 515)
    rsi_db = web.get_data_yahoo(ticker,
                              start = datetime.datetime(old_datetime.year, old_datetime.month, old_datetime.day),
                              end = datetime.datetime(datetime.date.today().year, datetime.date.today().month, datetime.date.today().day))
    rsi_db = rsi_db[["Close"]]
    rsi_db.rename(columns = {"Close":"Price"}, inplace = True)
    rsi_db['RSI'] = computeRSI(rsi_db["Price"], 14)

    one_year_ago = datetime.datetime.now() - datetime.timedelta(days = 365)
    one_year_ago = one_year_ago.strftime('%Y-%m-%d')

    rsi_db = rsi_db.loc[one_year_ago:]
    # get latest daily RSI
    rsi_last = rsi_db.iloc[-1]
    # plot and save 1-year graph
    plt.style.use('seaborn-dark')
    plt.style.use('tableau-colorblind10')
    fig = plt.figure(figsize = (20,12))
    ax1 = plt.plot(rsi_db["RSI"])
    ax1 = plt.axhline(30, linestyle = '--', color = 'green')
    ax1 = plt.axhline(70, linestyle = '--', color = 'red')
    ax1 = plt.title(f"{ticker} RSI for the last 1 year", fontsize = 20)
    ax1 = plt.xlabel("Date", fontsize = 18)
    ax1 = plt.ylabel("RSI", fontsize = 18)
    ax1 = plt.legend(["RSI", "Oversold", "Overbought"],prop = {"size":20}, loc = "upper left")
    plt.grid(True)
    plt.savefig('saved_figure.png')

    return rsi_last.round(2)
