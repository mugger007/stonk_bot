import pandas_datareader as web
import datetime
import matplotlib.pyplot as plt
import matplotlib as mpl

def last_year_macd(
    ticker: str):
    old_datetime = datetime.datetime.now() - datetime.timedelta(days = 515)
    macd_db = web.get_data_yahoo(ticker,
                              start = datetime.datetime(old_datetime.year, old_datetime.month, old_datetime.day),
                              end = datetime.datetime(datetime.date.today().year, datetime.date.today().month, datetime.date.today().day))
    macd_db = macd_db[["Close"]]
    macd_db.rename(columns = {"Close":"Price"}, inplace = True)
    macd_db["12EMA"] = macd_db["Price"].ewm(span = 12).mean()
    macd_db["26EMA"] = macd_db["Price"].ewm(span = 26).mean()
    macd_db['MACD'] = macd_db["12EMA"] - macd_db["26EMA"]
    macd_db["signal"] = macd_db['MACD'].ewm(span = 9).mean()

    one_year_ago = datetime.datetime.now() - datetime.timedelta(days = 365)
    one_year_ago = one_year_ago.strftime('%Y-%m-%d')

    macd_db = macd_db.loc[one_year_ago:]
    # get latest daily MACD
    macd_last = macd_db.iloc[-1]
    # plot and save 1-year graph
    plt.style.use('seaborn-dark')
    plt.style.use("tableau-colorblind10")
    fig = plt.figure(figsize = (20,12))
    ax1 = plt.plot(macd_db['MACD'])
    ax1 = plt.plot(macd_db["signal"])
    ax1 = plt.title(f"{ticker} MACD vs Signal for the last 1 year", fontsize = 20)
    ax1 = plt.xlabel("Date", fontsize = 18)
    ax1 = plt.legend(["MACD", "Signal"],prop = {"size":20}, loc = "upper left")
    plt.grid(True)
    plt.savefig('saved_figure.png')

    return macd_last.round(2)
