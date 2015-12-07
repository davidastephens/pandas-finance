pandas-finance
=================

High level API for access to and analysis of financial data.

.. image:: https://travis-ci.org/davidastephens/pandas-finance.svg?branch=master
    :target: https://travis-ci.org/davidastephens/pandas-finance

.. image:: https://coveralls.io/repos/davidastephens/pandas-finance/badge.svg?branch=master
    :target: https://coveralls.io/r/davidastephens/pandas-finance

.. image:: https://readthedocs.org/projects/pandas-finance/badge/?version=latest
    :target: http://pandas-finance.readthedocs.org/en/latest/

Installation
------------

Install via pip

.. code-block:: shell

   $ pip install pandas-finance

Usage
-----

.. code-block:: python

   from pandas_finance import Equity
   aapl = Equity('AAPL')
   aapl.annual_dividend
   aapl.dividend_yield
   aapl.price
   aapl.options
   aapl.hist_vol(30)
   aapl.rolling_hist_vol(30)

Data is automatically cached for 1 hr using requests_cache.

See the `pandas-finance documentation <http://pandas-finance.readthedocs.org/>`_ for more details.
