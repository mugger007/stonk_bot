import requests
import json
from datetime import datetime, timedelta
import pandas as pd

def news(
    ticker: str):
    date_today = datetime.today().strftime('%Y-%m-%d')
    date_ystd = datetime.today() - timedelta(days = 1)
    date_ystd = date_ystd.strftime('%Y-%m-%d')

    # get first name of company. because ticker/full name usually gives very little news
    url_0 = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={}&region=1&lang=en".format(ticker.upper())
    result = requests.get(url_0).json()
    for x in result['ResultSet']['Result']:
        if x['symbol'] == ticker.upper():
            ticker_name = x['name'].split(' ', 1)[0]
            ticker_name = ticker_name + ' OR ' + ticker.upper()

    # get top popular news on the company
    url_1 = ('https://newsapi.org/v2/everything?'
        f'qInTitle={ticker_name}&'
        f'from={date_ystd}&'
        'sortBy=popularity&'
        'language=en&'
        'apiKey=1e6a51a80dc842d9b8bcd754333f2167')

    response = requests.get(url_1).json()
    top_news = pd.json_normalize(response['articles'])
    try:
        top_news_links = top_news['url'][:3].tolist()
        return top_news_links
    except:
        return False
