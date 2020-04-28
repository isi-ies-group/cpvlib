# -*- coding: utf-8 -*-
"""
Created on Wed Apr  8 17:01:27 2020

@author: Ruben
"""

import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

import pvlib

data = pd.read_csv('../datos/InsolightMay2019.csv',
                   index_col='Date Time', parse_dates=True, encoding='latin1')
data.index = data.index.tz_localize('Europe/Madrid')

data = data.rename(columns={
    'DNI (W/m2)': 'dni',
    'DII (W/m2)': 'dii',
    'GII (W/m2)': 'gii',
    'T_Amb (°C)': 'temp_air',
    'Wind Speed (m/s)': 'wind_speed',
    'T_Backplane (°C)': 'temp_cell',
    'ISC_measured_IIIV (A)': 'isc_35',
    'ISC_measured_Si (A)': 'isc_si',
})


location = pvlib.location.Location(
    latitude=40.4, longitude=-3.7, altitude=695, tz='Europe/Madrid')

solar_zenith = location.get_solarposition(data.index).zenith
solar_azimuth = location.get_solarposition(data.index).azimuth

data['aoi'] = pvlib.irradiance.aoi(surface_tilt=30, surface_azimuth=180,
                                   solar_zenith=solar_zenith, solar_azimuth=solar_azimuth)

# filtro 3 días soleados
# data = data['2019-05-30':'2019-06-01']

data['isc_si/gii'] = data['isc_si'] / data['gii']
data = data.replace(np.inf, np.nan).dropna()

# filtra outliers
# data_filt = data[(np.abs(stats.zscore(data['isc_si/gii'])) < 0.2)]

data_filt = data[data['isc_si/gii'].rolling(window='2Min').std() < 0.0002]
# data_filt = data_filt[data_filt['isc_si/gii'] < 0.0021]

data_filt['isc_si/gii'].plot(style='.')

data_filt.plot.scatter(y='isc_si/gii', x='aoi', ylim=[0, 0.006], xlim=[0, 90])

#%% Ajuste lineal por tramos
def linear(x, a, b):
    return a * x + b

data_filt_aoi1 = data_filt.query('aoi<55')
data_filt_aoi2 = data_filt.query('55<aoi<80')

(a1, b1), pcov = curve_fit(
    linear, data_filt_aoi1['aoi'], data_filt_aoi1['isc_si/gii'])
(a2, b2), pcov = curve_fit(
    linear, data_filt_aoi2['aoi'], data_filt_aoi2['isc_si/gii'])

isc_si_est1 = linear(data_filt_aoi1['aoi'], a1, b1)
isc_si_est2 = linear(data_filt_aoi2['aoi'], a2, b2)

residuals1 = data_filt_aoi1['isc_si/gii'] - isc_si_est1
RMSE1 = np.sqrt(((residuals1) ** 2).mean())
print(f'RMSE1={RMSE1} a1={a1} b1={b1}')
plt.hist(residuals1, bins=100)

residuals2 = data_filt_aoi2['isc_si/gii'] - isc_si_est2
RMSE2 = np.sqrt(((residuals2) ** 2).mean())
print(f'RMSE2={RMSE2} a2={a2} b2={b2}')
plt.hist(residuals2, bins=100)

ax = data_filt.plot.scatter(y='isc_si/gii', x='aoi',
                            ylim=[0, 0.006], xlim=[0, 90])
ax.plot(data_filt_aoi1['aoi'], isc_si_est1, 'r-')
ax.plot(data_filt_aoi2['aoi'], isc_si_est2, 'r-')

#%% define la funcion por tramos
def get_aoi_util_factor(aoi, aoi_thld, aoi_limit, a1, b1, a2, b2):
    if isinstance(aoi, (int, float)):
        aoi = float(aoi)
    else:
        aoi = aoi.values
    condlist = [aoi < aoi_thld, (aoi_thld <= aoi) & (aoi < aoi_limit)]
    funclist = [lambda x:x*b1+a1, lambda x:x*b2+a2]
    
    return np.piecewise(aoi, condlist, funclist)

aoi_thld, aoi_limit = 55, 80

ax = data_filt.plot.scatter(y='isc_si/gii', x='aoi',
                            ylim=[0, 0.006], xlim=[0, 90])
ax.plot(data_filt['aoi'], get_aoi_util_factor(data_filt['aoi'], aoi_thld, aoi_limit), 'r.')

uf_aoi_ast = get_aoi_util_factor(0, aoi_thld, aoi_limit)
uf_aoi_norm = get_aoi_util_factor(data['aoi'], aoi_thld, aoi_limit) / uf_aoi_ast

plt.plot(data['aoi'], uf_aoi_norm, '.')
