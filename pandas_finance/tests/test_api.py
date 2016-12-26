import datetime

import pandas.util.testing as tm
import pandas as pd

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
        self.assertEqual(self.aapl.annual_dividend, 0.57 * 4)

    def test_dividends(self):
        self.assertEqual(self.aapl.dividends[datetime.date(2015, 11, 5)], 0.52)

    def test_price(self):
        self.assertIsInstance(self.aapl.price, float)

    def test_sector(self):
        self.assertEqual(self.aapl.sector, 'Consumer Goods')

    def test_employees(self):
        self.assertGreater(self.aapl.employees, 100000)

    def test_industry(self):
        self.assertEqual(self.aapl.industry, 'Electronic Equipment')

    def test_name(self):
        self.assertEqual(self.aapl.name, 'Apple Inc.')


class TestOptionChain(tm.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.aapl = Equity('AAPL')
        cls.options = OptionChain(cls.aapl)

    def test_options(self):
        self.assertIsInstance(self.options.all_data, pd.DataFrame)

    def test_calls(self):
        self.assertIsInstance(self.options.calls, pd.DataFrame)
        self.assertTrue((self.options.calls.index.get_level_values('Type') == 'calls').all())

    def test_puts(self):
        self.assertIsInstance(self.options.puts, pd.DataFrame)
        self.assertTrue((self.options.puts.index.get_level_values('Type') == 'puts').all())

    def test_near_calls(self):
        self.assertIsInstance(self.options.near_calls, pd.DataFrame)
        self.assertTrue((self.options.near_calls.index.get_level_values('Type') == 'calls').all())

    def test_near_puts(self):
        self.assertIsInstance(self.options.near_puts, pd.DataFrame)
        self.assertTrue((self.options.near_puts.index.get_level_values('Type') == 'puts').all())


class TestOption(tm.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.aapl = Equity('AAPL')
        cls.options = OptionChain(cls.aapl)

    def test_options(self):
        self.options.all_data
