import alpaca_trade_api as tradeapi
import pandas as pd
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import *

class TradeBot:
    def __init__(self):
        self.api = None
        self.account = None
        self.message = MIMEMultipart()
        self.stock1 = 'AAPL'
        self.stock2 = 'GOOGL'
        self.wide_spread = 0
        self.thin_spread = 0
        self.spread_curr = 0
        self.number_of_shares = 0


    def trading_algo_init(self):
        # Specify paper trading environment
        os.environ['APCA_API_BASE_URL'] = 'https://paper-api.alpaca.markets'

        # Access Alpaca account
        self.api = tradeapi.REST(API_KEY, SECRET_KEY, api_version='v2')
        self.account = self.api.get_account()

        # Setup MIME
        self.message['From'] = 'Trading Bot'
        self.message['To'] = RECEIVER_EMAIL
        self.message['Subject'] = 'Pairs Trading Algo'  # The subject line

        #return done

    def prep_historical_data(self):
        # Selection of stocks
        days = 1000


        # Put Hisrorical Data into variables
        stock1_barset = self.api.get_barset(self.stock1, 'day', limit=days)
        stock2_barset = self.api.get_barset(self.stock2, 'day', limit=days)
        stock1_bars = stock1_barset[self.stock1]
        stock2_bars = stock2_barset[self.stock2]

        # Grab stock1 data and put in to a array
        data_1 = []
        times_1 = []
        for i in range(days):
            stock1_close = stock1_bars[i].c
            stock1_time = stock1_bars[i].t
            data_1.append(stock1_close)
            times_1.append(stock1_time)

        # Grab stock2 data and put in to an array
        data_2 = []
        times_2 = []
        for i in range(days):
            stock2_close = stock2_bars[i].c
            stock2_time = stock1_bars[i].t
            data_2.append(stock2_close)
            times_2.append(stock2_time)

        # Putting them together
        hist_close = pd.DataFrame(data_1, columns=[self.stock1])
        hist_close[self.stock2] = data_2

        # Current Spread between the two stocks
        stock1_curr = data_1[days-1]
        stock2_curr = data_2[days-1]
        self.spread_curr = (stock1_curr-stock2_curr)

        # Moving Average of the two stocks
        move_avg_days = 5

        # Moving averge for stock1
        stock1_last = []
        for i in range(move_avg_days):
            stock1_last.append(data_1[(days-1)-i])

        stock1_hist = pd.DataFrame(stock1_last)

        stock1_mavg = stock1_hist.mean()

        # Moving average for stock2
        stock2_last = []
        for i in range(move_avg_days):
            stock2_last.append(data_2[(days-1)-i])
        stock2_hist = pd.DataFrame(stock2_last)
        stock2_mavg = stock2_hist.mean()

        # Sread_avg
        spread_avg = min(stock1_mavg - stock2_mavg)

        # Spread_factor
        spreadFactor = .01
        self.wide_spread = spread_avg*(1+spreadFactor)
        self.thin_spread = spread_avg*(1-spreadFactor)

        # Calc_of_shares_to_trade
        cash = float(self.account.buying_power)
        limit_stock1 = cash//stock1_curr
        limit_stock2 = cash//stock2_curr
        self.number_of_shares = int(min(limit_stock1, limit_stock2)/2)
        print(self.number_of_shares)

    def trade(self):
        # Trading_algo
        portfolio = self.api.list_positions()
        clock = self.api.get_clock()

        if clock.is_open == True:
            if bool(portfolio) == False:
                # detect a wide spread
                if self.spread_curr > self.wide_spread:
                    # short top stock
                    self.api.submit_order(symbol=self.stock1, qty=self.number_of_shares, side='sell', type='market', time_in_force='day')

                    # Long bottom stock
                    self.api.submit_order(symbol=self.stock2, qty=self.number_of_shares, side='buy', type='market', time_in_force='day')
                    mail_content = "Trades have been made, short top stock and long bottom stock"

                # detect a tight spread
                elif self.spread_curr < self.thin_spread:
                    # long top stock
                    self.api.submit_order(symbol=self.stock1, qty=self.number_of_shares, side='buy', type='market', time_in_force='day')

                    # short bottom stock
                    self.api.submit_order(symbol=self.stock2, qty=self.number_of_shares, side='sell', type='market', time_in_force='day')
                    mail_content = "Trades have been made, long top stock and short bottom stock"
            else:
                wideTradeSpread = spread_avg * (1+spreadFactor + .03)
                thinTradeSpread = spread_avg * (1+spreadFactor - .03)
                if self.spread_curr <= wideTradeSpread and self.spread_curr >= thinTradeSpread:
                    self.api.close_position(self.stock1)
                    self.api.close_position(self.stock2)
                    mail_content = "Position has been closed"
                else:
                    mail_content = "No trades were made, position remains open"
                    pass
        else:
            mail_content = "The Market is Closed"

        print(mail_content)

        # The body and the attachments for the mail
        self.message.attach(MIMEText(mail_content, 'plain'))

        # Create SMTP session for sending the mail
        session = smtplib.SMTP('smtp.gmail.com', 587)  # use gmail with port
        session.starttls()  # enable security

        # login with mail_id and password
        session.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = self.message.as_string()
        session.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, text)
        session.quit()

        done = 'Mail Sent'

        return done

trade_bot = TradeBot()
trade_bot.trading_algo_init()
trade_bot.prep_historical_data()
trade_bot.trade()