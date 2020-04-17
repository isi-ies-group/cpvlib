# -*- coding: utf-8 -*-
"""
Created on Fri Apr 17 00:20:08 2020

@author: Ruben
"""
import pandas as pd

vdf_raw = pd.read_csv('dec12_apr14_fadriquePlant_pandas.zip',
                      index_col='timedate', parse_dates=True).resample('T').mean()
