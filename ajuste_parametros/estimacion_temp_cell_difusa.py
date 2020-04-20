# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 01:37:10 2020

@author: Ruben
"""
import pandas as pd
import numpy as np
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
    'PMP_estimated_IIIV (W)': 'pmp_35',
    'PMP_estimated_Si (W)': 'pmp_si'
})

location = pvlib.location.Location(
    latitude=40.4, longitude=-3.7, altitude=695, tz='Europe/Madrid')

solar_zenith = location.get_solarposition(data.index).zenith
solar_azimuth = location.get_solarposition(data.index).azimuth

data['aoi'] = pvlib.irradiance.aoi(surface_tilt=30, surface_azimuth=180,
                                   solar_zenith=solar_zenith, solar_azimuth=solar_azimuth)

FF = 0.7
# https://doi.org/10.5281/zenodo.3346823
# 0.1 m2, 572 (12x48) micro-cells + 4x 6"(15.24 cm) Si-cells in series
# https://doi.org/10.5281/zenodo.3349781
# 35 rango IV: 0.7 A, 35 V @DNI 900 W/m2
# Si rango IV: 1.7 A, 2.2 V @GNI 950 W/m2 y DNI/GNI=0.7

data_low_aoi = data.query('aoi<55')
data_upp_aoi = data.query('55<aoi<80')

data_low_aoi['voc_si'] = (data_low_aoi.pmp_si / data_low_aoi.isc_si) / FF
data_upp_aoi['voc_si'] = (data_upp_aoi.pmp_si / data_upp_aoi.isc_si) / FF

data_low_aoi.query('990<gii<1010').voc_si.hist(bins=50, histtype='step', label='low aoi')
data_upp_aoi.query('400<gii<500').voc_si.hist(bins=50, histtype='step', label='upp aoi')

Ns = 4
beta = -2.2e-3

Vocr = 1.75
data_low_aoi['tcell_si'] = 25 + (data_low_aoi.voc_si - Vocr)/(Ns*beta)
ax=data_low_aoi.plot.scatter(x='temp_air', y='tcell_si', label='Si')
data_low_aoi.plot.scatter(ax=ax, x='temp_air', y='temp_cell', color='r', label='III-V')

Vocr = 1.85
data_upp_aoi['tcell_si'] = 25 + (data_upp_aoi.voc_si - Vocr)/(Ns*beta)
ax=data_upp_aoi.plot.scatter(x='temp_air', y='tcell_si', label='Si')
data_upp_aoi.plot.scatter(ax=ax, x='temp_air', y='temp_cell', color='r', label='III-V')