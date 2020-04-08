# -*- coding: utf-8 -*-
"""
Created on Wed Apr  8 16:01:01 2020

@author: Ruben
"""
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

from pvlib.temperature import sapm_module

#%% lee datos campaña 2019-05
data = pd.read_csv('../InsolightMay2019.csv', index_col='Date Time',
                   parse_dates=True, encoding='latin1')
data.index = data.index.tz_localize('Europe/Madrid')

data = data.rename(columns={
    'DNI (W/m2)': 'dni',
    'DII (W/m2)': 'dii',
    'GII (W/m2)': 'gii',
    'T_Amb (°C)': 'temp_air',
    'Wind Speed (m/s)': 'wind_speed',
    'T_Backplane (°C)': 'temp_cell_35',
    'ISC_measured_IIIV (A)': 'isc35',
    'ISC_measured_Si (A)': 'iscSi',
})

#%% 
def f(meteo_inputs, a ,b):
    poa_global, temp_air, wind_speed = meteo_inputs
    return sapm_module(poa_global, temp_air, wind_speed, a, b)

param,_ = curve_fit(f, (data.dii, data.temp_air, data.wind_speed), data.temp_cell_35)

a, b = param
temp_cell_35_est = sapm_module(data.dii, data.temp_air, data.wind_speed, a, b)

plt.hist2d(data.temp_cell_35, temp_cell_35_est, bins=30)
plt.grid(True)

plt.hist(data.temp_cell_35 - temp_cell_35_est, bins=100)
