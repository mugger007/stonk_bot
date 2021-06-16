import pandas_datareader as web
import datetime
import matplotlib.pyplot as plt
import matplotlib as mpl

def last_year_sma(
    ticker: str):
    old_datetime = datetime.datetime.now() - datetime.timedelta(days = 515)
    sma_db = web.get_data_yahoo(ticker,
                              start = datetime.datetime(old_datetime.year, old_datetime.month, old_datetime.day),
                              end = datetime.datetime(datetime.date.today().year, datetime.date.today().month, datetime.date.today().day))
    sma_db = sma_db[["Close"]]
    sma_db.rename(columns = {"Close":"Price"}, inplace = True)
    sma_db["100MA"] = sma_db["Price"].rolling(window = 100).mean()
    sma_db["50MA"] = sma_db["Price"].rolling(window = 50).mean()
    sma_db["20MA"] = sma_db["Price"].rolling(window = 20).mean()

    one_year_ago = datetime.datetime.now() - datetime.timedelta(days = 365)
    one_year_ago = one_year_ago.strftime('%Y-%m-%d')

    sma_db = sma_db.loc[one_year_ago:]
    # get latest daily SMA
    sma_last = sma_db.iloc[-1]
    # plot and save 1-year graph
    plt.style.use('seaborn-dark')
    plt.style.use("tableau-colorblind10")
    fig = plt.figure(figsize = (20,12))
    ax1 = plt.plot(sma_db["Price"])
    ax1 = plt.plot(sma_db["100MA"])
    ax1 = plt.plot(sma_db["50MA"])
    ax1 = plt.plot(sma_db["20MA"])
    ax1 = plt.title(f"{ticker} daily closing price for the last 1 year", fontsize = 20)
    ax1 = plt.xlabel("Date", fontsize = 18)
    ax1 = plt.ylabel("Price", fontsize = 18)
    ax1 = plt.legend(["Price", "100-day SMA", "50-day SMA", "20-day SMA"],prop = {"size":20}, loc = "upper left")
    plt.grid(True)
    plt.savefig('saved_figure.png')

    return sma_last.round(2)
