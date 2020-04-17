# -*- coding: utf-8 -*-
"""
Created on Fri Apr 17 00:20:08 2020

@author: Ruben
"""
import pandas as pd

vdf_raw = pd.read_csv('../datos/2012-12_2014-04_fadriquePlant.zip',
                      index_col='timedate', parse_dates=True).resample('T').mean()

#%% intrepid
int_raw = pd.read_csv('../datos/2014-05_2015-05_intrepidTracker.zip',
                      index_col='datetime', parse_dates=True)
