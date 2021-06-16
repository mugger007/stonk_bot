# [Stonk Bot](http://t.me/stonkkk_bot)

Current version: 2.1

A Telegram bot (@stonkkk_bot) that helps you keep track of your stock portfolio with daily notifications, news and technical analysis.

### Key Features

* Get Latest Price (and % Change): obtain the latest price and 1-day % price change of any US-listed stock, including those in your watchlist
* Get Latest News: obtain the latest popular news of any US-listed stock, including those in your watchlist
* Watchlist: view, add or delete any US-listed stock. For Daily Summary and Notification (see below)
* Technical Analysis: use various popular technical indicators and their graphs to help in your decision making

Autonomous features (available only if you have a watchlist)
* Daily Summary: provides the closing price and 1-day % price change for a US-listed stock at the end of day (at 4pm ET) (and maybe some snark remarks)
* Notification: provides an alert on significant movement(s) based on the available technical indicators for a US-listed stock. E.g. if the stock is overbought or oversold based on the daily RSI (at 12pm and 4pm ET). Intraday (5-min interval) RSI notification is also now available.

### Setup

If you wish to create your own version, clone this repo to your enviroment and follow the steps below.  

1. Obtain your unique Telegram Bot Api Token and Heroku App URL and insert them into `bot.py`.

```python
TOKEN = 'TELEGRAM_BOT_TOKEN'
HEROKU_URL = 'HEROKU_APP_URL'
```

2. Create a database (and a table within it) using PostgreSQL. There are many ways to do this - check out this [article from Towards Data Science](https://towardsdatascience.com/a-practical-guide-to-getting-set-up-with-postgresql-a1bf37a0cfd7) for a quick guide. The table in the database should have 2 columns: `user_id` (user's unique Telegram ID) and `ticker` (ticker symbol).

3. Obtain the credentials of your database and insert them into `config.py`.

```python
host = 'HOST_URL' 
port = 'PORT_NO'
database = 'DATABASE_ID'
user = 'USER_ID'
password = 'PASSWORD'
```

4. Insert your table name into `dbhelper.py`.

```python
user_tb = Table('TABLE_NAME', metadata, autoload = True)
```

5. You are almost set! Now you just need to deploy it on an external server (in our case, Heroku) so that the bot may run 24/7*. Follow the steps provided in this [article from Towards Data Science](https://towardsdatascience.com/how-to-deploy-a-telegram-bot-using-heroku-for-free-9436f89575d2). In addition to the steps in the aforementioned article, include these in your terminal:

```python
heroku ps:scale web=1
```
to scale your app to one running dyno, basically meaning you have one server running your app currently.

```python
heroku logs --tail
```
to display current log entries, which would be useful in debugging. 

*Do note that when an app on Heroku has only one web dyno and that dyno does not receive any traffic in 1 hour, the dyno goes to sleep. When someone accesses the app, the dyno manager will automatically wake up the web dyno to run the web process type.

### Bug/Feature Request

If you find a bug, kindly open an issue [here](https://github.com/mugger007/stonk-bot/issues/new?assignees=&labels=&template=bug_report.md&title=).

If you would like to request a new feature, feel free to do so by opening an issue [here](https://github.com/mugger007/stonk-bot/issues/new?assignees=&labels=&template=feature_request.md&title=).
