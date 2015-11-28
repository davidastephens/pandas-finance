import datetime

import pandas.util.testing as tm

from pandas_finance import Equity, Option, OptionChain


class TestEquity(tm.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.aapl = Equity('AAPL')
        cls.date = datetime.date(2013, 1, 25)

    def test_equity_price(self):
        self.assertAlmostEqual(self.aapl.close[self.date], 439.88, 2)

    def test_historical_vol(self):
        vol = self.aapl.hist_vol(30, end_date=self.date)
        self.assertAlmostEqual(vol, 0.484, 3)

    def test_options(self):
        self.assertIsInstance(self.aapl.options, OptionChain)

    def test_annual_dividend(self):
        self.assertEqual(self.aapl.annual_dividend, 0.52*4)

    def test_dividends(self):
        self.assertEqual(self.aapl.dividends[datetime.date(2015,11,5)],0.52)

    def test_price(self):
        self.assertIsInstance(self.aapl.price, float)

class TestOptionChain(tm.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.aapl = Equity('AAPL')
        cls.options = OptionChain(cls.aapl)

    def test_options(self):
        self.options.all_data

class TestOption(tm.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.aapl = Equity('AAPL')
        cls.options = OptionChain(cls.aapl)

    def test_options(self):
        self.options.all_data


