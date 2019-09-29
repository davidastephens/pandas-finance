import datetime
import math

import pandas as pd
import pandas_datareader.data as pdr
import requests_cache
import empyrical

TRADING_DAYS = 252
CACHE_HRS = 1
START_DATE = datetime.date(1990, 1, 1)
QUERY_STRING = 'https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker}?lang=en-US&region=US&modules={modules}&corsDomain=finance.yahoo.com'
YQL_STRING = 'https://query.yahooapis.com/v1/public/yql?env=store://datatables.org/alltableswithkeys&format=json&q={yql}'
YQL_QUOTES = 'select * from yahoo.finance.quotes where symbol = "{ticker}"'


class Equity(object):
    def __init__(self, ticker, session=None):
        self.ticker = ticker

        if session:
            self._session = session
        else:
            self._session = self._get_session()

    def _get_session(self):
        return requests_cache.CachedSession(cache_name='pf-cache',
                                            backend='sqlite',
                                            expire_after=datetime.timedelta(
                                                hours=CACHE_HRS))

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
        return pdr.get_data_yahoo(self.ticker, session=self._session,
                                  start=START_DATE)

    @property
    def dividends(self):
        actions = pdr.get_data_yahoo_actions(self.ticker, session=self._session,
                                             start=START_DATE)
        dividends = actions[actions['action'] == 'DIVIDEND']['value']
        dividends.name = 'Dividends'
        return dividends

    @property
    def annual_dividend(self):
        if 'trailingAnnualDividendRate' in self.quotes.index:
            return self.quotes['trailingAnnualDividendRate']
        else:
            return 0

    @property
    def dividend_yield(self):
        return self.annual_dividend / self.price

    @property
    def price(self):
        return self.quotes['price']

    @property
    def closed(self):
        "Market is closed or open"
        return self.quotes['marketState'].lower() == 'closed'

    @property
    def currency(self):
        return self.quotes['currency']

    @property
    def market_cap(self):
        return float(self.quotes['marketCap'])

    @property
    def shares_os(self):
        return int(self.quotes['sharesOutstanding'])

    def hist_vol(self, days, end_date=None):
        days = int(days)
        if end_date:
            data = self.returns[:end_date]
        else:
            data = self.returns
        data = data.iloc[-days:]
        return data.std() * math.sqrt(TRADING_DAYS)

    def rolling_hist_vol(self, days, end_date=None):
        days = int(days)
        if end_date:
            data = self.returns[:end_date]
        else:
            data = self.returns
        return data.rolling(days).std() * math.sqrt(TRADING_DAYS)

    @property
    def profile(self):
        response = self._session.get(QUERY_STRING.format(ticker=self.ticker,
                                                         modules='assetProfile')).json()
        asset_profile = response['quoteSummary']['result'][0]['assetProfile']
        del asset_profile['companyOfficers']
        profile = pd.DataFrame.from_dict(asset_profile, orient='index')[0]
        profile.name = ""
        profile.index = [name.capitalize() for name in profile.index]
        rename = {'Fulltimeemployees': 'Full Time Employees'}
        profile.rename(index=rename, inplace=True)

        return profile

    @property
    def quotes(self):
        return pdr.get_quote_yahoo(self.ticker, session=self._session).T[self.ticker]

    @property
    def quote(self):
        return self.quotes

    @property
    def sector(self):
        return self.profile['Sector']

    @property
    def industry(self):
        return self.profile['Industry']

    @property
    def employees(self):
        return self.profile['Full Time Employees']

    @property
    def name(self):
        return self.quotes['longName']

    def alpha_beta(self, index, start=None, end=None):
        index_rets = Equity(index).returns
        rets = self.returns
        data = pd.DataFrame()
        data['Index'] = index_rets
        data['Rets'] = rets
        data = data.fillna(0)

        if start:
            data = data[start:]
        if end:
            data = data[start:end]

        return empyrical.alpha_beta(data['Rets'], data['Index'])

    def beta(self, index, start=None, end=None):
        alpha, beta = self.alpha_beta(index, start, end)
        return beta

    def alpha(self, index, start=None, end=None):
        alpha, beta = self.alpha_beta(index, start, end)
        return alpha

    def vwap(self, end_date=None, days=30):
        days = int(days)
        if end_date:
            data = self.trading_data[:end_date]
        else:
            data = self.trading_data
        data = data.iloc[-days:]
        return (data['Close'] * data['Volume']).sum() / data['Volume'].sum()

    def hist_vol_by_days(self, end_date=None, min_days=10, max_days=600):
        "Returns the historical vol for a range of trading days ending on end_date."
        min_days = int(min_days)
        max_days = int(max_days)
        if end_date:
            returns = self.returns[:end_date]
        else:
            returns = self.returns

        output = {}
        for i in range(min_days, max_days):
            output[i] = returns[-i:].std()*math.sqrt(TRADING_DAYS)

        return pd.Series(output)


class Option(object):
    def __init__(self):
        pass


class OptionChain(object):
    def __init__(self, underlying):
        self.underlying = underlying
        self._session = self.underlying._session
        self._pdr = pdr.Options(self.underlying.ticker, 'yahoo',
                                session=self._session)

    @property
    def all_data(self):
        return self._pdr.get_all_data()

    @property
    def calls(self):
        data = self.all_data
        mask = data.index.get_level_values('Type') == 'calls'
        return data[mask]

    @property
    def puts(self):
        data = self.all_data
        mask = data.index.get_level_values('Type') == 'puts'
        return data[mask]

    @property
    def near_puts(self):
        return self._pdr._chop_data(self.puts, 5, self.underlying.price)

    @property
    def near_calls(self):
        return self._pdr._chop_data(self.calls, 5, self.underlying.price)

    def __getattr__(self, key):
        if hasattr(self._pdr, key):
            return getattr(self._pdr, key)

    def __dir__(self):
        return sorted(set((dir(type(self)) + list(self.__dict__) +
                           dir(self._pdr))))
