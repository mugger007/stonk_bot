import pandas_datareader as web
import datetime
import matplotlib.pyplot as plt
import matplotlib as mpl

def last_year_ema(
    ticker: str):
    old_datetime = datetime.datetime.now() - datetime.timedelta(days = 515)
    ema_db = web.get_data_yahoo(ticker,
                              start = datetime.datetime(old_datetime.year, old_datetime.month, old_datetime.day),
                              end = datetime.datetime(datetime.date.today().year, datetime.date.today().month, datetime.date.today().day))
    ema_db = ema_db[["Close"]]
    ema_db.rename(columns = {"Close":"Price"}, inplace = True)
    ema_db["100MA"] = ema_db["Price"].ewm(span = 100).mean()
    ema_db["50MA"] = ema_db["Price"].ewm(span = 50).mean()
    ema_db["20MA"] = ema_db["Price"].ewm(span = 20).mean()

    one_year_ago = datetime.datetime.now() - datetime.timedelta(days = 365)
    one_year_ago = one_year_ago.strftime('%Y-%m-%d')

    ema_db = ema_db.loc[one_year_ago:]
    # get latest daily EMA
    ema_last = ema_db.iloc[-1]
    # plot and save 1-year graph
    plt.style.use('seaborn-dark')
    plt.style.use("tableau-colorblind10")
    fig = plt.figure(figsize = (20,12))
    ax1 = plt.plot(ema_db["Price"])
    ax1 = plt.plot(ema_db["100MA"])
    ax1 = plt.plot(ema_db["50MA"])
    ax1 = plt.plot(ema_db["20MA"])
    ax1 = plt.title(f"{ticker} daily closing price for the last 1 year", fontsize = 20)
    ax1 = plt.xlabel("Date", fontsize = 18)
    ax1 = plt.ylabel("Price", fontsize = 18)
    ax1 = plt.legend(["Price", "100-day EMA", "50-day EMA", "20-day EMA"],prop = {"size":20}, loc = "upper left")
    plt.grid(True)
    plt.savefig('saved_figure.png')

    return ema_last.round(2)
