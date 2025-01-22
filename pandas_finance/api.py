import datetime
import math
import json

import pandas as pd
from pandas import DataFrame, Series
from pandas_datareader.yahoo.quotes import YahooQuotesReader

import pandas_datareader.data as pdr
import requests_cache
import empyrical

TRADING_DAYS = 252
CACHE_HRS = 1
START_DATE = datetime.date(1990, 1, 1)
QUERY_STRING = "https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker}?lang=en-US&region=US&modules={modules}&corsDomain=finance.yahoo.com"
HEADERS = {
    "Connection": "keep-alive",
    "Expires": str(-1),
    "Upgrade-Insecure-Requests": str(1),
    # Google Chrome:
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    ),
}
_DEFAULT_PARAMS = {
    "lang": "en-US",
    "corsDomain": "finance.yahoo.com",
    ".tsrc": "finance",
}


class FixedYahooQuotesReader(YahooQuotesReader):
    def __init__(self, *args, crumb=None, **kwargs):
        super(FixedYahooQuotesReader, self).__init__(*args, **kwargs)
        self.crumb = crumb
    def params(self, symbol):
        params = super().params(symbol)
        params.update({"crumb": self.crumb})
        return params
    def _read_lines(self, out):
        data = json.loads(out.read())["quoteResponse"]["result"][0]
        idx = data.pop('symbol')
        data["price"] = data["regularMarketPrice"]
        return Series(data)


class Equity(object):
    def __init__(self, ticker, session=None):
        self.ticker = ticker

        if session:
            self._session = session
        else:
            self._session = self._get_session()
            with self._session.cache_disabled():
                self.crumb = self._session.get(
                    'https://query1.finance.yahoo.com/v1/test/getcrumb').text

    def _get_session(self):
        session = requests_cache.CachedSession(
            cache_name="pf-cache",
            backend="sqlite",
            expire_after=datetime.timedelta(hours=CACHE_HRS),
        )
        session.headers.update(HEADERS)
        with session.cache_disabled():
            session.get('https://fc.yahoo.com')
        return session

    @property
    def options(self):
        return OptionChain(self)

    @property
    def close(self):
        """Returns pandas series of closing price"""
        return self.trading_data["Close"]

    @property
    def adj_close(self):
        """Returns pandas series of closing price"""
        return self.trading_data["Adj Close"]

    @property
    def returns(self):
        return self.adj_close.pct_change()

    @property
    def trading_data(self):
        return pdr.get_data_yahoo(self.ticker, session=self._session, start=START_DATE)

    @property
    def actions(self):
        return pdr.get_data_yahoo_actions(
            self.ticker, session=self._session, start=START_DATE
        )

    @property
    def dividends(self):
        actions = self.actions
        dividends = actions[actions["action"] == "DIVIDEND"]["value"]
        dividends.name = "Dividends"
        return dividends

    @property
    def splits(self):
        actions = self.actions
        splits = actions[actions["action"] == "SPLIT"]["value"]
        splits.name = "Splits"
        return splits

    @property
    def annual_dividend(self):
        if "forwardAnnualDividendRate" in self.quotes.index:
            return self.quotes["forwardAnnualDividendRate"]
        elif "trailingAnnualDividendRate" in self.quotes.index:
            return self.quotes["trailingAnnualDividendRate"]
        else:
            return 0

    @property
    def dividend_yield(self):
        return self.annual_dividend / self.price

    @property
    def price(self):
        return self.quotes["price"]

    @property
    def closed(self):
        "Market is closed or open"
        return self.quotes["marketState"].lower() == "closed"

    @property
    def currency(self):
        return self.quotes["currency"]

    @property
    def market_cap(self):
        return float(self.quotes["marketCap"])

    @property
    def shares_os(self):
        return int(self.quotes["sharesOutstanding"])

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
        response = self._session.get(
            QUERY_STRING.format(ticker=self.ticker, modules="assetProfile")
        ).json()
        asset_profile = response["quoteSummary"]["result"][0]["assetProfile"]
        del asset_profile["companyOfficers"]
        profile = pd.DataFrame.from_dict(asset_profile, orient="index")[0]
        profile.name = ""
        profile.index = [name.capitalize() for name in profile.index]
        rename = {"Fulltimeemployees": "Full Time Employees"}
        profile.rename(index=rename, inplace=True)

        return profile

    @property
    def quotes(self):
        return FixedYahooQuotesReader(self.ticker, session=self._session, crumb=self.crumb).read()

    @property
    def quote(self):
        return self.quotes

    @property
    def sector(self):
        return self.profile["Sector"]

    @property
    def industry(self):
        return self.profile["Industry"]

    @property
    def employees(self):
        return self.profile["Full Time Employees"]

    @property
    def name(self):
        return self.quotes["longName"]

    def alpha_beta(self, index, start=None, end=None):
        index_rets = Equity(index).returns
        rets = self.returns
        data = pd.DataFrame()
        data["Index"] = index_rets
        data["Rets"] = rets
        data = data.fillna(0)

        if start:
            data = data[start:]
        if end:
            data = data[start:end]

        return empyrical.alpha_beta(data["Rets"], data["Index"])

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
        return (data["Close"] * data["Volume"]).sum() / data["Volume"].sum()

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
            output[i] = returns[-i:].std() * math.sqrt(TRADING_DAYS)

        return pd.Series(output)


class Option(object):
    def __init__(self):
        pass


class OptionChain(object):
    def __init__(self, underlying):
        self.underlying = underlying
        self._session = self.underlying._session
        self._pdr = pdr.Options(self.underlying.ticker, "yahoo", session=self._session)

    @property
    def all_data(self):
        return self._pdr.get_all_data()

    @property
    def calls(self):
        data = self.all_data
        mask = data.index.get_level_values("Type") == "calls"
        return data[mask]

    @property
    def puts(self):
        data = self.all_data
        mask = data.index.get_level_values("Type") == "puts"
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
        return sorted(set((dir(type(self)) + list(self.__dict__) + dir(self._pdr))))
