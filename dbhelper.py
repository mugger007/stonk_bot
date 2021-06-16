from sqlalchemy import *
from config import host, port, database, user, password

class DBHelper:

    def __init__(self):
        conn_str = f"postgresql://{user}:{password}@{host}/{database}"
        global engine
        engine = create_engine(conn_str)
        metadata = MetaData(bind = engine)
        global user_tb
        user_tb = Table('TABLE_NAME', metadata, autoload = True)
    # add row (ticker and user_id) to database
    def add_item(self, ticker, user_id):
        query = insert(user_tb).values(user_id = user_id, ticker = ticker)
        connection = engine.connect()
        ResultProxy = connection.execute(query)
    # delete row (ticker and user_id) from database
    def delete_item(self, ticker, user_id):
        query = delete(user_tb).where(user_tb.c.user_id == user_id, user_tb.c.ticker == ticker)
        connection = engine.connect()
        ResultProxy = connection.execute(query)
    # select ticker from database given user_id
    def get_items(self, user_id):
        query = select(user_tb.c.ticker).where(user_tb.c.user_id == user_id)
        connection = engine.connect()
        result = connection.execute(query)
        return [r.ticker for r in result]
    # select user_id from database given ticker
    def get_users(self, ticker):
        query = select(user_tb.c.user_id).where(user_tb.c.ticker == ticker)
        connection = engine.connect()
        result = connection.execute(query)
        return [r.user_id for r in result]
    # select all user_id from database
    def get_user_list(self):
        query = select(user_tb.c.user_id).distinct(user_tb.c.user_id)
        connection = engine.connect()
        result = connection.execute(query)
        return [x.user_id for x in result]
    # select all ticker from database
    def get_ticker_list(self):
        query = select(user_tb.c.ticker).distinct(user_tb.c.ticker)
        connection = engine.connect()
        result = connection.execute(query)
        return [x.ticker for x in result]
