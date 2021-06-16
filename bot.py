import os
import logging
import datetime
import random
from telegram.ext import (
    Updater,
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    Filters,
    JobQueue,
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from ticker_quote import last_quote
from ticker_price_change import calculate_price_change
from ticker_news import news
from check_ticker import valid_ticker
from dbhelper import DBHelper
from ticker_sma import last_year_sma
from ticker_ema import last_year_ema
from ticker_macd import last_year_macd
from ticker_rsi import last_year_rsi
from ticker_notification import (
    rsi_notification,
    intraday_rsi_notif,
    macd_notification,
    sma_notification,
    ema_notification
)
# stages
FIRST, QUOTE, TOP_NEWS, SAVE_WATCHLIST, WATCHLIST, SMA, EMA, MACD, RSI = range(9)
# callback data
ONE, THREE, FOUR, FIVE, SIX, SEVEN, EIGHT, NINE, TEN, ELEVEN, TWELVE, THIRTEEN, FOURTEEN, FIFTEEN = range(14)

MODE = os.environ.get("MODE", "webhook") # change to 'polling' for testing/non-deployment to Heroku
PORT = int(os.environ.get('PORT', '8443'))

db = DBHelper()

# enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = 'TELEGRAM_BOT_TOKEN'
HEROKU_URL = 'HEROKU_APP_URL'

main_keyboard = [
        [
        InlineKeyboardButton("Get Latest Price (and % Change)", callback_data = str(ONE)),
        InlineKeyboardButton("Get Latest News", callback_data = str(THREE)),
        ],
        [
        InlineKeyboardButton("Technical Analysis", callback_data = str(ELEVEN)),
        InlineKeyboardButton("Watchlist", callback_data = str(FOUR)),
        ],
    ]

ta_keyboard = [
        [
        InlineKeyboardButton("More Technical Analysis", callback_data = str(ELEVEN)),
        InlineKeyboardButton("Back", callback_data = str(EIGHT))
        ],
    ]

# send introductory message when command /start is issued
def start(update, context):

    user = update.message.from_user
    first_name = update.message.chat.first_name
    chat_id = update.message.chat_id

    context.user_data['ticker_list'] = db.get_items(chat_id)

    logger.info("User %s started the conversation.", user.first_name)

    reply_markup = InlineKeyboardMarkup(main_keyboard)

    update.message.reply_text(f"Hello {user.first_name}! Use the command /about to find out more Stonk Bot. Choose an option:", reply_markup = reply_markup)
    # tell ConversationHandler that we are in state `FIRST` now
    return FIRST

# send messages on features and updates when command /about is issued
def about(update, context):

    user = update.message.from_user
    first_name = update.message.chat.first_name

    logger.info("User %s started About.", user.first_name)

    reply_markup = InlineKeyboardMarkup(main_keyboard)

    message_1 = """Thank you for using Stonk Bot. Here are the key features:
        \n\u2022 Get Latest Price (and % Change): obtain the latest price and 1-day % price change of any US-listed stock, including those in your watchlist
        \n\u2022 Get Latest News: obtain the latest popular news of any US-listed stock, including those in your watchlist
        \n\u2022 Watchlist: view, add or delete any US-listed stock. For Notification and Daily Summary
        \n\u2022 Technical Analysis: use various popular technical indicators and their graphs to help in your decision making
        """
    message_2 = """Autonomous features (available only if you have a watchlist):
        \n\u2022 Daily Summary: provides the closing price and 1-day % price change for a US-listed stock at the end of day (at 4pm ET) (and maybe some snark remarks)
        \n\u2022 Notification: provides an alert on significant movement(s) based on the available technical indicators for a US-listed stock. E.g. if the stock is overbought or oversold based on the daily RSI (at 12pm and 4pm ET). Intraday (5-min interval) RSI notification is also now available.
        """
    message_3 = """Current version - 2.1.
        \nUpdates:
        \n\u2022 Merged 'Get Quote' and 'Get Price Change' into 'Get Latest Price (and % Change)'
        \n\u2022 Changed the descriptions for the TA graphs
        \n\u2022 Included intra-day RSI notification - based on prices in 5-min interval. Notification will be triggered only once a day (i.e. when the stock goes above RSI of 70 and/or below RSI of 30) to avoid getting spammed
        \n\u2022 Changed the SMA/EMA notification conditions - notification will be triggered if the latest price goes below or above the SMA/EMA line(s)
        """
    update.message.reply_text(message_1)
    update.message.reply_text(message_2)
    update.message.reply_text(message_3, reply_markup = reply_markup)

    return FIRST

# return main options when user selects 'Back'
def start_over(update, context):

    query = update.callback_query
    query.answer()

    user = query.message.chat
    first_name = user.first_name

    logger.info("User %s re-started the conversation.", user.first_name)

    reply_markup = InlineKeyboardMarkup(main_keyboard)

    query.edit_message_text(
        text = f"Welcome back {first_name}, choose an option:", reply_markup = reply_markup)

    return FIRST

# check if user has existing watchlist and wants to use it
def get_quote(update, context):

    query = update.callback_query
    query.answer()
    context.user_data['choice'] = query.data
    choice = context.user_data['choice']

    keyboard = [
            [
            InlineKeyboardButton("Yes", callback_data = str(NINE)),
            InlineKeyboardButton("No", callback_data = str(TEN))
            ],
            [
            InlineKeyboardButton("Back", callback_data = str(EIGHT))
            ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if not context.user_data['ticker_list']:
        query.edit_message_text(
            text = "Type in ticker(s) - seperate by a comma for multiple tickers:"
            )

        if choice == str(ONE):
            return QUOTE
        elif choice == str(THREE):
            return TOP_NEWS
        elif choice == str(TWELVE):
            return SMA
        elif choice == str(THIRTEEN):
            return EMA
        elif choice == str(FOURTEEN):
            return MACD
        elif choice == str(FIFTEEN):
            return RSI

    else:
        query.edit_message_text(
            text = "Would you like to use your saved watchlist?", reply_markup = reply_markup)
        return WATCHLIST

# re-route user who wants to use existing watchlist back to the intended action
def use_watchlist_yes(update, context):
    query = update.callback_query
    query.answer()
    choice = context.user_data['choice']
    context.user_data['use_watchlist_no'] = "NO"

    if choice == str(ONE):
        return return_quote(update, context)
    elif choice == str(THREE):
        return return_news(update, context)
    elif choice == str(TWELVE):
        return return_sma(update, context)
    elif choice == str(THIRTEEN):
        return return_ema(update, context)
    elif choice == str(FOURTEEN):
        return return_macd(update, context)
    elif choice == str(FIFTEEN):
        return return_rsi(update, context)

# re-route user who does not want to use existing watchlist back to the intended action
def use_watchlist_no(update, context):
    query = update.callback_query
    query.answer()
    choice = context.user_data['choice']
    context.user_data['use_watchlist_no'] = "YES"

    query.edit_message_text(
        text = "Type in ticker(s) - seperate by a comma for multiple tickers:"
        )

    if choice == str(ONE):
        return QUOTE
    elif choice == str(THREE):
        return TOP_NEWS
    elif choice == str(TWELVE):
        return SMA
    elif choice == str(THIRTEEN):
        return EMA
    elif choice == str(FOURTEEN):
        return MACD
    elif choice == str(FIFTEEN):
        return RSI

# provide latest price and % price change
def return_quote(update, context):

    reply_markup = InlineKeyboardMarkup(main_keyboard)
    # if user has no watchlist and/or chooses to manually input ticker(s)
    if (not context.user_data['ticker_list']) or (context.user_data['use_watchlist_no'] == "YES"):
        chat_id = update.message.chat.id
        ticker_list = update.message.text.upper()
        ticker_list = [x.strip() for x in ticker_list.split(',')]

        invalid_ticker = []
        # check for valid ticker(s)
        for ticker in ticker_list:
            if valid_ticker(ticker) is False:
                invalid_ticker.append(ticker)

        if not invalid_ticker:
            context.user_data['temp_ticker_list'] = ticker_list
            context.user_data['use_watchlist_no'] = "NO"
            update.message.reply_text("Here is/are the latest price(s) and % change(s):")

        else:
            invalid_ticker_list_str = ', '.join(invalid_ticker)
            invalid_ticker_list_str = invalid_ticker_list_str
            context.user_data['use_watchlist_no'] = "YES"
            update.message.reply_text(f"The ticker(s) {invalid_ticker_list_str} is/are invalid. Please re-enter valid ticker(s):")

            return QUOTE
    # if user uses existing watchlist
    else:
        query = update.callback_query
        chat_id = query.message.chat.id
        context.user_data['temp_ticker_list'] = context.user_data['ticker_list']
        query.edit_message_text(
            text = "Here is/are the latest price(s) and % change(s):"
            )

    for ticker in context.user_data['temp_ticker_list']:
        pct_chng, _ = calculate_price_change(ticker)
        quote = last_quote(ticker)
        message = f"{ticker} - latest price: {quote}; changed by {pct_chng}%!"
        if pct_chng > 0:
            message += ' 🟢 '
        if pct_chng < 0:
            message += ' 🔴 '
        if pct_chng > 3:
            message += random.choice(('To the f*cking moon!', 'Are you Warren Buffett?', 'Is this the next meme stock?'))
        if pct_chng < -3:
            message += random.choice(('Panicking yet?', 'Are you the bagholder?', 'Did you even do your due diligence?'))
        context.bot.send_message(chat_id = chat_id, text = message)

    context.bot.send_message(chat_id = chat_id, text = "Hello, what would you like to do next:", reply_markup = reply_markup)

    return FIRST

# provide latest popular English news
def return_news(update, context):

    reply_markup = InlineKeyboardMarkup(main_keyboard)
    # if user has no watchlist and/or chooses to manually input ticker(s)
    if (not context.user_data['ticker_list']) or (context.user_data['use_watchlist_no'] == "YES"):
        chat_id = update.message.chat.id
        ticker_list = update.message.text.upper()
        ticker_list = [x.strip() for x in ticker_list.split(',')]

        invalid_ticker = []
        # check for valid ticker(s)
        for ticker in ticker_list:
            if valid_ticker(ticker) is False:
                invalid_ticker.append(ticker)

        if not invalid_ticker:
            context.user_data['temp_ticker_list'] = ticker_list
            context.user_data['use_watchlist_no'] == "NO"
            update.message.reply_text("Here are the latest news:")

        else:
            invalid_ticker_list_str = ', '.join(invalid_ticker)
            invalid_ticker_list_str = invalid_ticker_list_str
            context.user_data['use_watchlist_no'] = "YES"
            update.message.reply_text(f"The ticker(s) {invalid_ticker_list_str} is/are invalid. Please re-enter valid ticker(s):")

            return TOP_NEWS
    # if user uses existing watchlist
    else:
        query = update.callback_query
        chat_id = query.message.chat.id
        context.user_data['temp_ticker_list'] = context.user_data['ticker_list']
        query.edit_message_text(
            text = "Here are the latest news:"
            )

    for ticker in context.user_data['temp_ticker_list']:
        top_news_links = news(ticker)
        if top_news_links is not False:
            context.bot.send_message(chat_id = chat_id, text = f"Latest news on {ticker}:")
            for i in top_news_links:
                context.bot.send_message(chat_id = chat_id, text = i)
        else:
            context.bot.send_message(chat_id = chat_id, text = f"There are no latest news on {ticker}:")

    context.bot.send_message(chat_id = chat_id, text = "Hello, what would you like to do next:", reply_markup = reply_markup)

    return FIRST

def watchlist_home(update, context):

    query = update.callback_query
    query.answer()
    # keyboard for users with no watchlist
    keyboard_1 = [
            [
            InlineKeyboardButton("Create Watchlist", callback_data = str(FIVE)),
            InlineKeyboardButton("Back", callback_data = str(EIGHT))
            ],
    ]

    reply_markup_1 = InlineKeyboardMarkup(keyboard_1)
    # keyboard for users with existing watchlist
    keyboard_2 = [
            [
            InlineKeyboardButton("Add to Watchlist", callback_data = str(SIX)),
            InlineKeyboardButton("Delete from Watchlist", callback_data = str(SEVEN)),
            ],
            [
            InlineKeyboardButton("Back", callback_data = str(EIGHT))
            ]
    ]

    reply_markup_2 = InlineKeyboardMarkup(keyboard_2)

    if not context.user_data['ticker_list']:
        query.edit_message_text(
        text = "You do not have a watchlist yet. Select an option:", reply_markup = reply_markup_1)

    else:
        tickers = ", ".join(context.user_data['ticker_list'])
        query.edit_message_text(
        text = f"You currently have {tickers} in your watchlist. Select an option:", reply_markup = reply_markup_2)

    return WATCHLIST

def watchlist_action(update, context):

    query = update.callback_query
    query.answer()
    choice = query.data

    if choice == str(FIVE):

        context.user_data['watchlist_action'] = "CREATE"
        query.edit_message_text(
            text = "Type in ticker(s) - seperate by a comma for multiple tickers:"
        )

    elif choice == str(SIX):

        context.user_data['watchlist_action'] = "ADD"
        query.edit_message_text(
            text = "Type in ticker(s) to add - seperate by a comma for multiple tickers:"
        )

    elif choice == str(SEVEN):

        context.user_data['watchlist_action'] = "DELETE"
        query.edit_message_text(
            text = "Type in ticker(s) to delete - seperate by a comma for multiple tickers:"
        )

    return SAVE_WATCHLIST

# make change(s) to watchlist database and reflecting change(s) to user
def save_watchlist(update, context):

    chat_id = update.message.chat_id

    reply_markup = InlineKeyboardMarkup(main_keyboard)

    ticker_list = update.message.text.upper()
    context.user_data['temp_ticker_list'] = [x.strip() for x in ticker_list.split(',')]

    invalid_ticker = []

    for ticker in context.user_data['temp_ticker_list']:
        # check for valid ticker(s)
        if valid_ticker(ticker) is False:
            invalid_ticker.append(ticker)
        else:
            if context.user_data['watchlist_action'] == "CREATE":
                db.add_item(ticker, chat_id)
            if context.user_data['watchlist_action'] == "ADD":
                if ticker in context.user_data['ticker_list']:
                    update.message.reply_text(f"The ticker {ticker} is already in your watchlist. Please re-enter valid ticker(s):")
                    return SAVE_WATCHLIST
                else:
                    db.add_item(ticker, chat_id)
            if context.user_data['watchlist_action'] == "DELETE":
                if ticker not in context.user_data['ticker_list']:
                    update.message.reply_text(f"The ticker {ticker} is not in your watchlist. Please re-enter valid ticker(s):")
                    return SAVE_WATCHLIST
                else:
                    db.delete_item(ticker, chat_id)

    if not invalid_ticker:

        ticker_list_str = ', '.join(context.user_data['temp_ticker_list'])

        if context.user_data['watchlist_action'] == "CREATE":
            update.message.reply_text(f"You have successfully added {ticker_list_str} to your watchlist.")

        if context.user_data['watchlist_action'] == "ADD":
            update.message.reply_text(f"You have successfully added {ticker_list_str} to your watchlist.")

        if context.user_data['watchlist_action'] == "DELETE":
            update.message.reply_text(f"You have successfully deleted {ticker_list_str} from your watchlist.")

        items = db.get_items(chat_id)
        context.user_data['ticker_list'] = items

        update.message.reply_text("Hello, what would you like to do next:", reply_markup = reply_markup)

        return FIRST

    else:
        invalid_ticker_list_str = ', '.join(invalid_ticker)
        invalid_ticker_list_str = invalid_ticker_list_str
        update.message.reply_text(f"The ticker(s) {invalid_ticker_list_str} is/are invalid. Please re-enter valid ticker(s):")

        return SAVE_WATCHLIST

def technical_analysis_home(update, context):

    query = update.callback_query
    query.answer()

    keyboard = [
            [
            InlineKeyboardButton("SMA", callback_data = str(TWELVE)),
            InlineKeyboardButton("EMA", callback_data = str(THIRTEEN)),
            ],
            [
            InlineKeyboardButton("MACD", callback_data = str(FOURTEEN)),
            InlineKeyboardButton("RSI", callback_data = str(FIFTEEN)),
            ],
            [
            InlineKeyboardButton("Back", callback_data = str(EIGHT)),
            ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text(
    text = f"Choose a technical analysis:", reply_markup = reply_markup)

    return FIRST

# provide latest daily SMA
def return_sma(update, context):

    reply_markup = InlineKeyboardMarkup(ta_keyboard)
    # if user has no watchlist and/or chooses to manually input ticker(s)
    if (not context.user_data['ticker_list']) or (context.user_data['use_watchlist_no'] == "YES"):
        chat_id = update.message.chat.id
        ticker_list = update.message.text.upper()
        ticker_list = [x.strip() for x in ticker_list.split(',')]

        invalid_ticker = []
        # check for valid ticker(s)
        for ticker in ticker_list:
            if valid_ticker(ticker) is False:
                invalid_ticker.append(ticker)

        if not invalid_ticker:
            context.user_data['temp_ticker_list'] = ticker_list
            context.user_data['use_watchlist_no'] = "NO"
            update.message.reply_text("Here is/are the SMA graph(s) for the past 1 year:")

        else:
            invalid_ticker_list_str = ', '.join(invalid_ticker)
            invalid_ticker_list_str = invalid_ticker_list_str
            context.user_data['use_watchlist_no'] = "YES"
            update.message.reply_text(f"The ticker(s) {invalid_ticker_list_str} is/are invalid. Please re-enter valid ticker(s):")

            return SMA
    # if user uses existing watchlist
    else:
        query = update.callback_query
        chat_id = query.message.chat.id
        context.user_data['temp_ticker_list'] = context.user_data['ticker_list']
        query.edit_message_text(
            text = "Here is/are the SMA graph(s) for the past 1 year:"
            )

    for ticker in context.user_data['temp_ticker_list']:
        sma_last = last_year_sma(ticker)
        context.bot.send_message(chat_id = chat_id,
            text = f"Latest price for {ticker}: {sma_last['Price']} \n100-day SMA: {sma_last['100MA']} \n50-day SMA: {sma_last['50MA']} \n20-day SMA: {sma_last['20MA']}")
        context.bot.sendPhoto(chat_id = chat_id, photo = open('saved_figure.png', 'rb'))

    context.bot.send_message(chat_id = chat_id, text = "Hello, what would you like to do next:", reply_markup = reply_markup)

    return FIRST

# provide latest daily EMA
def return_ema(update, context):

    reply_markup = InlineKeyboardMarkup(ta_keyboard)
    # if user has no watchlist and/or chooses to manually input ticker(s)
    if (not context.user_data['ticker_list']) or (context.user_data['use_watchlist_no'] == "YES"):
        chat_id = update.message.chat.id
        ticker_list = update.message.text.upper()
        ticker_list = [x.strip() for x in ticker_list.split(',')]

        invalid_ticker = []
        # check for valid ticker(s)
        for ticker in ticker_list:
            if valid_ticker(ticker) is False:
                invalid_ticker.append(ticker)

        if not invalid_ticker:
            context.user_data['temp_ticker_list'] = ticker_list
            context.user_data['use_watchlist_no'] = "NO"
            update.message.reply_text("Here is/are the EMA graph(s) for the past 1 year:")

        else:
            invalid_ticker_list_str = ', '.join(invalid_ticker)
            invalid_ticker_list_str = invalid_ticker_list_str
            context.user_data['use_watchlist_no'] = "YES"
            update.message.reply_text(f"The ticker(s) {invalid_ticker_list_str} is/are invalid. Please re-enter valid ticker(s):")

            return EMA
    # if user uses existing watchlist
    else:
        query = update.callback_query
        chat_id = query.message.chat.id
        context.user_data['temp_ticker_list'] = context.user_data['ticker_list']
        query.edit_message_text(
            text = "Here is/are the EMA graph(s) for the past 1 year:"
            )

    for ticker in context.user_data['temp_ticker_list']:
        ema_last = last_year_ema(ticker)
        context.bot.send_message(chat_id = chat_id,
            text = f"Latest price for {ticker}: {ema_last['Price']} \n100-day EMA: {ema_last['100MA']} \n50-day EMA: {ema_last['50MA']} \n20-day EMA: {ema_last['20MA']}")
        context.bot.sendPhoto(chat_id = chat_id, photo = open('saved_figure.png', 'rb'))

    context.bot.send_message(chat_id = chat_id, text = "Hello, what would you like to do next:", reply_markup = reply_markup)

    return FIRST

# provide latest daily MACD
def return_macd(update, context):

    reply_markup = InlineKeyboardMarkup(ta_keyboard)
    # if user has no watchlist and/or chooses to manually input ticker(s)
    if (not context.user_data['ticker_list']) or (context.user_data['use_watchlist_no'] == "YES"):
        chat_id = update.message.chat.id
        ticker_list = update.message.text.upper()
        ticker_list = [x.strip() for x in ticker_list.split(',')]

        invalid_ticker = []
        # check for valid ticker(s)
        for ticker in ticker_list:
            if valid_ticker(ticker) is False:
                invalid_ticker.append(ticker)

        if not invalid_ticker:
            context.user_data['temp_ticker_list'] = ticker_list
            context.user_data['use_watchlist_no'] = "NO"
            update.message.reply_text("Here is/are the MACD graph(s) for the past 1 year:")

        else:
            invalid_ticker_list_str = ', '.join(invalid_ticker)
            invalid_ticker_list_str = invalid_ticker_list_str
            context.user_data['use_watchlist_no'] = "YES"
            update.message.reply_text(f"The ticker(s) {invalid_ticker_list_str} is/are invalid. Please re-enter valid ticker(s):")

            return MACD
    # if user uses existing watchlist
    else:
        query = update.callback_query
        chat_id = query.message.chat.id
        context.user_data['temp_ticker_list'] = context.user_data['ticker_list']
        query.edit_message_text(
            text = "Here is/are the MACD graph(s) for the past 1 year:"
            )

    for ticker in context.user_data['temp_ticker_list']:
        macd_last = last_year_macd(ticker)
        context.bot.send_message(chat_id = chat_id,
            text = f"Latest price for {ticker}: {macd_last['Price']} \nMACD: {macd_last['MACD']} \nSignal: {macd_last['signal']}")
        context.bot.sendPhoto(chat_id = chat_id, photo = open('saved_figure.png', 'rb'))

    context.bot.send_message(chat_id = chat_id, text = "Hello, what would you like to do next:", reply_markup = reply_markup)

    return FIRST

# provide latest daily RSI
def return_rsi(update, context):

    reply_markup = InlineKeyboardMarkup(ta_keyboard)
    # if user has no watchlist and/or chooses to manually input ticker(s)
    if (not context.user_data['ticker_list']) or (context.user_data['use_watchlist_no'] == "YES"):
        chat_id = update.message.chat.id
        ticker_list = update.message.text.upper()
        ticker_list = [x.strip() for x in ticker_list.split(',')]

        invalid_ticker = []
        # check for valid ticker(s)
        for ticker in ticker_list:
            if valid_ticker(ticker) is False:
                invalid_ticker.append(ticker)

        if not invalid_ticker:
            context.user_data['temp_ticker_list'] = ticker_list
            context.user_data['use_watchlist_no'] = "NO"
            update.message.reply_text("Here is/are the RSI graph(s) for the past 1 year:")

        else:
            invalid_ticker_list_str = ', '.join(invalid_ticker)
            invalid_ticker_list_str = invalid_ticker_list_str
            context.user_data['use_watchlist_no'] = "YES"
            update.message.reply_text(f"The ticker(s) {invalid_ticker_list_str} is/are invalid. Please re-enter valid ticker(s):")

            return RSI
    # if user uses existing watchlist
    else:
        query = update.callback_query
        chat_id = query.message.chat.id
        context.user_data['temp_ticker_list'] = context.user_data['ticker_list']
        query.edit_message_text(
            text = "Here is/are the RSI graph(s) for the past 1 year:"
            )

    for ticker in context.user_data['temp_ticker_list']:
        rsi_last = last_year_rsi(ticker)
        context.bot.send_message(chat_id = chat_id,
            text = f"Latest price for {ticker}: {rsi_last['Price']} \nRSI: {rsi_last['RSI']}")
        context.bot.sendPhoto(chat_id = chat_id, photo = open('saved_figure.png', 'rb'))

    context.bot.send_message(chat_id = chat_id, text = "Hello, what would you like to do next:", reply_markup = reply_markup)

    return FIRST

# provide daily summary on the closing price and 1-day % price change
def daily_summary(context):

    user_ids = db.get_user_list()

    for user_id in user_ids:
        ticker_list = db.get_items(user_id)
        context.bot.send_message(chat_id = user_id, text = "Here is your watchlist summary for today:")
        for ticker in ticker_list:
            pct_chng, _ = calculate_price_change(ticker)
            quote = last_quote(ticker)
            message = f"{ticker} - closing price: {quote}; changed by {pct_chng}%!"
            if pct_chng > 0:
                message += ' 🟢 '
            if pct_chng < 0:
                message += ' 🔴 '
            if pct_chng > 3:
                message += random.choice(('To the fucking moon!', 'Are you Warren Buffett?', 'Is this the next meme stock?'))
            if pct_chng < -3:
                message += random.choice(('Panicking yet?', 'Are you the bagholder?', 'Did you even do your due diligence?'))
            context.bot.send_message(chat_id = user_id, text = message)


# provide bi-daily TA-based notification
def notification(context):

    user_ids = db.get_user_list()

    for user_id in user_ids:
        ticker_list = db.get_items(user_id)
        for ticker in ticker_list:
            rsi_latest = rsi_notification(ticker)
            macd_diff_ystd, macd_diff_tdy = macd_notification(ticker)
            sma_20_ystd, sma_20_tdy, sma_50_ystd, sma_50_tdy, sma_100_ystd, sma_100_tdy, sma_price_ystd, sma_price_tdy = sma_notification(ticker)
            ema_20_ystd, ema_20_tdy, ema_50_ystd, ema_50_tdy, ema_100_ystd, ema_100_tdy, ema_price_ystd, ema_price_tdy = ema_notification(ticker)
            if rsi_latest > 70:
                message = f"{ticker} latest RSI ({rsi_latest}) is above 70 - it could be overbought."
                context.bot.send_message(chat_id = user_id, text = message)
            elif rsi_latest < 30:
                message = f"{ticker} latest RSI ({rsi_latest}) is below 30 - it could be oversold."
                context.bot.send_message(chat_id = user_id, text = message)

            if macd_diff_tdy > 0 and macd_diff_ystd < 0:
                message = f"{ticker} latest MACD line crossed above the signal line - it could be a bullish signal."
                context.bot.send_message(chat_id = user_id, text = message)
            elif macd_diff_tdy < 0 and macd_diff_ystd > 0:
                message = f"{ticker} latest MACD line crossed below the signal line - it could be a bearish signal."
                context.bot.send_message(chat_id = user_id, text = message)

            if sma_price_ystd < sma_20_ystd and sma_price_tdy > sma_20_tdy:
                message = f"{ticker} latest price crossed above the 20-day SMA."
                context.bot.send_message(chat_id = user_id, text = message)
            elif sma_price_ystd > sma_20_ystd and sma_price_tdy < sma_20_tdy:
                message = f"{ticker} latest price crossed below the 20-day SMA."
                context.bot.send_message(chat_id = user_id, text = message)

            if sma_price_ystd < sma_50_ystd and sma_price_tdy > sma_50_tdy:
                message = f"{ticker} latest price crossed above the 50-day SMA."
                context.bot.send_message(chat_id = user_id, text = message)
            elif sma_price_ystd > sma_50_ystd and sma_price_tdy < sma_50_tdy:
                message = f"{ticker} latest price crossed below the 50-day SMA."
                context.bot.send_message(chat_id = user_id, text = message)

            if sma_price_ystd < sma_100_ystd and sma_price_tdy > sma_100_tdy:
                message = f"{ticker} latest price crossed above the 100-day SMA."
                context.bot.send_message(chat_id = user_id, text = message)
            elif sma_price_ystd > sma_100_ystd and sma_price_tdy < sma_100_tdy:
                message = f"{ticker} latest price crossed below the 100-day SMA."
                context.bot.send_message(chat_id = user_id, text = message)

# empty the list of tickers that have met the condition(s) for intraday RSI notification on the prior day
def reset_notification_list(context):

    global rsi_notified_lessthanthirty
    rsi_notified_lessthanthirty = []
    global rsi_notified_morethanseventy
    rsi_notified_morethanseventy = []

    logger.info("Notification lists have been reset.")

# provide intraday RSI notification by checking the RSI in 5-min interval
def intraday_rsi_notification(context):

    day_no = datetime.datetime.today().weekday()

    # will only run on weekdays
    if day_no < 5:
        ticker_list = db.get_ticker_list()
        # obtain intraday RSI for each ticker in the database
        for ticker in ticker_list:
            rsi_latest = intraday_rsi_notif(ticker)
            # if condition is met, users with the ticker(s) will be notified
            # Users will be notified about each ticker's intraday RSI only once a day to avoid spamming
            if rsi_latest > 70 and ticker not in rsi_notified_morethanseventy:
                message = f"{ticker} latest INTRA-DAY RSI ({rsi_latest}) is above 70 - it could be overbought."
                user_ids = db.get_users(ticker)
                for user_id in user_ids:
                    context.bot.send_message(chat_id = user_id, text = message)
                rsi_notified_morethanseventy.append(ticker)

            elif rsi_latest < 30 and ticker not in rsi_notified_lessthanthirty:
                message = f"{ticker} latest INTRA-DAY RSI ({rsi_latest}) is below 30 - it could be oversold."
                user_ids = db.get_users(ticker)
                for user_id in user_ids:
                    context.bot.send_message(chat_id = user_id, text = message)
                rsi_notified_lessthanthirty.append(ticker)

# error handlers receive the raised TelegramError object in error
def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    # create the Updater and pass it bot's token
    # set use_context = True to use the new context based callbacks
    updater = Updater(TOKEN, use_context = True)

    # get the dispatcher to register handlers
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points = [CommandHandler('start', start)],
        states = {
            FIRST: [
                CallbackQueryHandler(get_quote, pattern = '^' + str(ONE) + '$'),
                CallbackQueryHandler(get_quote, pattern = '^' + str(THREE) + '$'),
                CallbackQueryHandler(watchlist_home, pattern = '^' + str(FOUR) + '$'),
                CallbackQueryHandler(start_over, pattern = '^' + str(EIGHT) + '$'),
                CallbackQueryHandler(technical_analysis_home, pattern = '^' + str(ELEVEN) + '$'),
                CallbackQueryHandler(get_quote, pattern = '^' + str(TWELVE) + '$'),
                CallbackQueryHandler(get_quote, pattern = '^' + str(THIRTEEN) + '$'),
                CallbackQueryHandler(get_quote, pattern = '^' + str(FOURTEEN) + '$'),
                CallbackQueryHandler(get_quote, pattern = '^' + str(FIFTEEN) + '$'),
            ],
            QUOTE: [MessageHandler(Filters.text & ~Filters.command, return_quote)],
            TOP_NEWS: [MessageHandler(Filters.text & ~Filters.command, return_news)],
            SAVE_WATCHLIST: [MessageHandler(Filters.text & ~Filters.command, save_watchlist)],
            SMA: [MessageHandler(Filters.text & ~Filters.command, return_sma)],
            EMA: [MessageHandler(Filters.text & ~Filters.command, return_ema)],
            MACD: [MessageHandler(Filters.text & ~Filters.command, return_macd)],
            RSI: [MessageHandler(Filters.text & ~Filters.command, return_rsi)],
            WATCHLIST: [
                CallbackQueryHandler(watchlist_action, pattern = '^' + str(FIVE) + '$'),
                CallbackQueryHandler(watchlist_action, pattern = '^' + str(SIX) + '$'),
                CallbackQueryHandler(watchlist_action, pattern = '^' + str(SEVEN) + '$'),
                CallbackQueryHandler(start_over, pattern = '^' + str(EIGHT) + '$'),
                CallbackQueryHandler(use_watchlist_yes, pattern = '^' + str(NINE) + '$'),
                CallbackQueryHandler(use_watchlist_no, pattern = '^' + str(TEN) + '$'),
            ],
        },
        fallbacks = [
            CommandHandler('start', start),
            CommandHandler('about', about)
            ],
    )

    dp.add_handler(conv_handler)
    dp.add_error_handler(error)

    job = updater.job_queue

    # prevent any potential duplicate jobs by removing them
    if 'daily_summary_job' in globals():
        daily_summary_job.schedule_removal()
    if 'notification_job_eod' in globals():
        notification_job_eod.schedule_removal()
    if 'notification_job_mid' in globals():
        notification_job_mid.schedule_removal()
    if 'notification_job_rsi' in globals():
        notification_job_rsi.schedule_removal()

    # set schedule for jobs
    daily_summary_job = job.run_daily(daily_summary, time = datetime.time(hour = 20, minute = 2, second = 0), days = (0, 1, 2, 3, 4))
    notification_job_eod = job.run_daily(notification, time = datetime.time(hour = 20, minute = 4, second = 0), days = (0, 1, 2, 3, 4))
    notification_job_mid = job.run_daily(notification, time = datetime.time(hour = 16, minute = 1, second = 0), days = (0, 1, 2, 3, 4))
    clear_rsi_notif_list = job.run_daily(reset_notification_list, time = datetime.time(hour = 13, minute = 29, second = 0), days = (0, 1, 2, 3, 4))
    notification_job_rsi = job.run_repeating(intraday_rsi_notification, interval = 300, first = datetime.time(13, 30, 0), last = datetime.time(20, 0, 0))

    # start the bot
    if MODE == 'webhook':
        # enable webhook
        updater.start_webhook(listen = "0.0.0.0",
                      port = PORT,
                      url_path = TOKEN,
                      webhook_url = HEROKU_URL + TOKEN)

    else:
        # enable polling
        updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
