import datetime
import unittest 
import pytest

import pandas as pd

from pandas_finance import Equity, Option, OptionChain


class TestEquity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.aapl = Equity('AAPL')
        cls.date = datetime.date(2013, 1, 25)
        cls.tsla = Equity('TSLA')

    def test_equity_price(self):
        self.assertAlmostEqual(self.aapl.close[self.date], 62.84, 2)

    def test_historical_vol(self):
        vol = self.aapl.hist_vol(30, end_date=self.date)
        self.assertAlmostEqual(vol, 0.484, 3)
    
    @pytest.mark.xfail(reason='Yahoo options api broken')
    def test_options(self):
        self.assertIsInstance(self.aapl.options, OptionChain)

    def test_annual_dividend(self):
        self.assertEqual(self.aapl.annual_dividend, 2.62)
        self.assertEqual(self.tsla.annual_dividend, 0)

    def test_dividends(self):
        self.assertEqual(self.aapl.dividends[datetime.date(2015, 11, 5)], 0.52)

    def test_dividends_no_data(self):
        self.assertEqual(len(self.tsla.dividends), 0)

    def test_price(self):
        self.assertIsInstance(self.aapl.price, float)

    def test_sector(self):
        self.assertEqual(self.aapl.sector, 'Technology')

    def test_employees(self):
        self.assertGreaterEqual(self.aapl.employees, 100000)

    def test_industry(self):
        self.assertEqual(self.aapl.industry, 'Consumer Electronics')

    def test_name(self):
        self.assertEqual(self.aapl.name, 'Apple Inc.')
    
    def test_quotes(self):
        self.assertIsInstance(self.aapl.quotes['price'], float)
    
    def test_quote(self):
        self.assertIsInstance(self.aapl.quote['price'], float)
    
    def test_shares_os(self):
        self.assertIsInstance(self.aapl.shares_os, int)
    
    def test_market_cap(self):
        self.assertIsInstance(self.aapl.market_cap , float)
    
    def test_closed(self):
        self.assertIsInstance(self.aapl.closed, bool)

    def test_currency(self):
        self.assertEqual(self.aapl.currency, 'USD')


class TestOptionChain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pytest.skip('Skip option tests due to broken yahoo api')
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


class TestOption(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.aapl = Equity('AAPL')
        pytest.skip('Skip option tests due to broken yahoo api')
        cls.options = OptionChain(cls.aapl)

    def test_options(self):
        self.options.all_data
