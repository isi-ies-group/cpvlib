# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 01:37:10 2020

@author: Ruben
"""
import pandas as pd
import numpy as np

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

FF = 0.5

data['voc_si'] = (data.pmp_si / data.isc_si) / FF

# https://doi.org/10.5281/zenodo.3346823
# 0.1 m2, 572 (12x48) micro-cells + 4x 6"(15.24 cm) Si-cells in series
# https://doi.org/10.5281/zenodo.3349781
# 35 rango IV: 0.7 A, 35 V @DNI 900 W/m2
# Si rango IV: 1.7 A, 2.2 V @GNI 950 W/m2 y DNI/GNI=0.7

data_low_aoi = data.query('aoi<55')
vocr_low_aoi = data_low_aoi.query('990<gii<1010 and 19<temp_air<21 and wind_speed<2').voc_si.mean()
iscr_low_aoi = data_low_aoi.query('990<gii<1010 and 19<temp_air<21 and wind_speed<2').isc_si.mean()

data_upp_aoi = data.query('55<aoi<80')
vocr_upp_aoi = data_upp_aoi.query('450<gii<550 and 19<temp_air<21 and wind_speed<2').voc_si.mean()
iscr_upp_aoi = data_upp_aoi.query('450<gii<550 and 19<temp_air<21 and wind_speed<2').isc_si.mean()

Ns = 4
beta = -2.2e-3

k = 1.38064852e-23 # m2 kg s-2 K-1
q = 1.60217662e-19 # coulombs

data_low_aoi['tcell_si'] = (data_low_aoi.voc_si - vocr_low_aoi + Ns*beta*298) / (Ns*(1*k/q)*np.log(data_low_aoi.isc_si/iscr_low_aoi)+ Ns*beta) - 273
ax=data_low_aoi.plot.scatter(x='temp_air', y='tcell_si', label='Si')
data_low_aoi.plot.scatter(ax=ax, x='temp_air', y='temp_cell', color='r', label='III-V')

data_upp_aoi['tcell_si'] = (data_upp_aoi.voc_si - vocr_upp_aoi + Ns*beta*298) / (Ns*(1*k/q)*np.log(data_upp_aoi.isc_si/iscr_upp_aoi)+ Ns*beta) - 273
ax=data_upp_aoi.plot.scatter(x='temp_air', y='tcell_si', label='Si')
data_upp_aoi.plot.scatter(ax=ax, x='temp_air', y='temp_cell', color='r', label='III-V')