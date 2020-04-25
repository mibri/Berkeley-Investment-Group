from __future__ import print_function
import time
import intrinio_sdk
from intrinio_sdk.rest import ApiException
from pprint import pprint
import datetime as dt
from datetime import date
from datetime import timedelta
import io
from collections import Counter
import numpy as np
from numpy import genfromtxt
import matplotlib.pyplot as plt
import pandas as pd

import requests, lxml
from lxml import html


class Stock_Yahoo:
    def __init__(self, ticker, start_date=dt.datetime.today().date(), end_date=dt.datetime.today().date(), frequency='daily', page_size=100):
        self.ticker = ticker
        self.frequency = frequency
        self.start_date = self.parse_date(start_date)
        self.end_date = self.parse_date(end_date)
        self.data = self.get_clean_yahoo()
        self.date_range_iter = self.daterange(start_date, end_date)

        self.prices = dict(
                            zip(map(lambda x: dt.datetime.strptime(x, '%Y-%m-%d').date(), self.data['Date']),
                                self.data['Adj Close'])
                        )
        self.start_price = self.prices[self.start_date]
#         self.end_price = self.prices[self.end_date]

    def parse_date(self, date):
        """ Parses string dates in format YYYY-MM-DD to datetime objects and adjusts them
        based on frequency. """

        """ TODO:
        - Account for holidays
        """
        if not isinstance(date, dt.date):
            date = dt.datetime.strptime(date, '%Y-%m-%d').date()

        if self.frequency == 'daily':
            day = date.weekday()
            if day >= 5:
                print('The day you chose is not a weekday.')
                date -= timedelta(days=day - day%4)

        elif self.frequency == 'weekly':
            day = date.weekday()
            if day > 0:
                print('Weeks start on a Monday')
                date -= timedelta(days=day)

        elif self.frequency == 'monthly':
            print('Month starts on the 1st')
            date = date.replace(day=1)
        return date

    def get_clean_yahoo(self):
        """ Creates the appropriate URL depending on ticker, frequency and dates """
        time_period = {'daily': '1d', 'weekly': '1wk', 'monthly': '1mo'}
        freq = time_period[self.frequency]
        start_date = int(time.mktime(self.start_date.timetuple()))
        end_date = int(time.mktime(self.end_date.timetuple()))
        yahoo_url = "https://query1.finance.yahoo.com/v7/finance/download/"+ self.ticker + "?period1=" + str(start_date) + "&period2=" + str(end_date) + "&interval=" + \
                    freq + "&events=history"
#         print(yahoo_url)
        data = pd.read_csv(yahoo_url)
        # sort in ascending date
        data = data.reindex(index=data.index[::-1])
        return data

    def display_close_price(self):
        #TODO: add start and end date arguments that maybe default to the start and end date
        #TODO: decide to standardize between either datetime64ns or datetime objects
            #chosen to have all dates in self.prices to be datetime objects
        #TODO: maybe we should make our own datetime actually
        plt.figure(figsize=(10,7))
        plt.title(self.ticker + " Stock Price")
        plt.plot(pd.to_datetime(self.data['Date']), list(self.prices.values()))
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.show()

    def get_performance(self, start=None, end=None):
        #TODO: Implementation depends on how we choose to represent datetime
        #TODO: Fix this thing, add holidays to daterange first
        if (start == None):
            start = self.start_date
        if (end == None):
            end = self.end_date

        max_ind = len(self.prices)
        curr_ind = 0
        gains = []
        for date in self.daterange(start, end):
            if ((date - self.start_date).total_seconds() < 0):
                gains.append(0)
            elif ((self.end_date - date).total_seconds() < 0):
                gains.append(0)
            elif (curr_ind >= max_ind):
                gains.append(0)
            else:
                gains.append(self.prices[date] - self.start_price)
                curr_ind += 1
        return np.array(gains)

    def daterange(self, start_date, end_date):
        #TODO: need to implement holidays, maybe even historical holidays, not really sure
        delta = timedelta(days=1)
        while start_date <= end_date:
            if (start_date.weekday() >= 5):
                start_date += delta
                continue
            yield start_date
            start_date += delta

    def get_df(self):
        return self.data

    def display_df(self, head=None):
        if head:
            display(self.data.head(head))
        else:
            display(self.data)

class Portfolio:
    def __init__(self, capital=1000):
        self.capital = float(capital)
        self.holdings = {}

    def buy(self, ticker='', start=date.today(), end=date.today()):
        newStock = Stock_Yahoo(ticker, start_date=start, end_date=end)
        self.holdings[newStock] = (start, end)

    def display_performance(self):
        min_date = min(self.holdings.values(), key = lambda x: x[0])[0]
        max_date = max(self.holdings.values(), key = lambda x: x[1])[1]

        perf = np.array([self.capital] * len(list(self.daterange(min_date, max_date))))
        for i in self.holdings:
            perf += i.get_performance(start=min_date, end=max_date)

        plt.title("Portfolio Performance")
        plt.plot(list(self.daterange(min_date, max_date)), perf)
        plt.xlabel("Date")
        plt.ylabel("$")
        plt.show()
        #some of the logic is wrong, so that if two stocks are seperated, then jumps to 1000 which is not right

    def daterange(self, start_date, end_date):
        delta = timedelta(days=1)
        while start_date <= end_date:
            if (start_date.weekday() >= 5):
                start_date += delta
                continue
            yield start_date
            start_date += delta
