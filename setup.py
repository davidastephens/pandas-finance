#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ast import parse
import os
from setuptools import setup, find_packages


NAME = 'pandas-finance'


def version():
    """Return version string."""
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)),
                           'pandas_finance',
                           '__init__.py')) as input_file:
        for line in input_file:
            if line.startswith('__version__'):
                return parse(line).body[0].value.s


def readme():
    with open('README.rst') as f:
        return f.read()

INSTALL_REQUIRES = (
        ['pandas', 'requests', 'requests-cache', 'beautifulsoup4', 'pandas-datareader>=0.2.2']
)

setup(
    name=NAME,
    version=version(),
    description="High level API for access to and analysis of financial data.",
    long_description=readme(),
    license='BSD License',
    author='David Stephens',
    author_email='david@davidstephens.io',
    url='https://github.com/davidastephens/pandas-finance',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'Operating System :: OS Independent',
        'Programming Language :: Cython',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Scientific/Engineering',
    ],
    keywords='data',
    install_requires=INSTALL_REQUIRES,
    dependency_links=['http://github.com/pydata/pandas-datareader/tarball/master#egg=pandas-datareader-0.2.2'],
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    test_suite='tests',
    zip_safe=False,
)
