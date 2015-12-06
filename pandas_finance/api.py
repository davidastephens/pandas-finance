import datetime
import math

import pandas as pd

import pandas_datareader.data as pdr
from pandas_datareader.data import Options

import requests_cache

TRADING_DAYS=252
CACHE_HRS = 1

class Equity(object):

    def __init__(self, ticker):
        self.ticker = ticker
        self._session = self._get_session()

    def _get_session(self):
        return requests_cache.CachedSession(cache_name='pf-cache', backend='sqlite', expire_after=datetime.timedelta(hours=CACHE_HRS))

    @property
    def options(self):
        return OptionChain(self)

    @property
    def close(self):
        """Returns pandas series of closing price"""
        return self.trading_data['Close']

    @property
    def adj_close(self):
        """Returns pandas series of closing price"""
        return self.trading_data['Adj Close']

    @property
    def returns(self):
        return self.adj_close.pct_change()

    @property
    def trading_data(self):
        return pdr.DataReader(self.ticker, 'yahoo', session=self._session)

    @property
    def dividends(self):
        actions = pdr.DataReader(self.ticker, 'yahoo-actions', session=self._session)
        dividends = actions[actions['action']=='DIVIDEND']
        dividends = dividends['value']
        dividends.name = 'Dividends'
        return dividends.sort_index()

    @property
    def annual_dividend(self):
        time_between = self.dividends.index[-1] - self.dividends.index[-2]
        times_per_year = round(365/time_between.days, 0)
        return times_per_year * self.dividends.values[-1]

    @property
    def dividend_yield(self):
        return self.annual_dividend/self.price

    @property
    def price(self):
        return pdr.get_quote_yahoo(self.ticker)['last'][0]

    def hist_vol(self, days, end_date=None):
        days = int(days)
        if end_date:
            data = self.returns[:end_date]
        else:
            data = self.returns
        data = data.iloc[-days:]
        return data.std()*math.sqrt(TRADING_DAYS)

    def rolling_hist_vol(self, days, end_date=None):
        if end_date:
            data = self.returns[:end_date]
        else:
            data = self.returns
        return pd.rolling_std(data, window=days)*math.sqrt(TRADING_DAYS)


class Option(object):
    def __init__(self):
        pass


class OptionChain(object):
    def __init__(self, underlying):
        self.underlying = underlying
        self._session = self.underlying._session
        self._pdr = pdr.Options(self.underlying.ticker, 'yahoo', session = self._session)

    @property
    def all_data(self):
        return self._pdr.get_all_data()

    @property
    def calls(self):
        data = self.all_data
        mask = data.index.get_level_values('Type')=='call'
        return data[mask]

    @property
    def puts(self):
        data = self.all_data
        mask = data.index.get_level_values('Type')=='put'
        return data[mask]

    @property
    def near_puts(self):
        return self._pdr.chop_data(self.puts, 5, self.underlying.price)

    @property
    def near_calls(self):
        return self._pdr.chop_data(self.calls, 5, self.underlying.price)

    def __getattr__(self,key):
        if hasattr(self._pdr, key):
            return getattr(self._pdr,key)

    def __dir__(self):
        return sorted(set((dir(type(self)) + list(self.__dict__) +
                                      dir(self._pdr))))
