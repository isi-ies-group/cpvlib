# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 00:42:10 2020

@author: Ruben
"""
import pandas as pd

import pvlib

data = pd.read_csv('InsolightMay2019.csv', index_col='Date Time', parse_dates=True, encoding='latin1')
data.index = data.index.tz_localize('Europe/Madrid')

data = data.rename(columns={
    'DNI (W/m2)':'dni',
    'DII (W/m2)':'dii',
    'GII (W/m2)':'gii',
    'T_Amb (°C)':'temp_air',
    'Wind Speed (m/s)':'wind_speed',
    'T_Backplane (°C)':'temp_cell',
    'ISC_measured_IIIV (A)':'isc_35',
    'ISC_measured_Si (A)':'isc_si',
    })

data['isc35/dii'] = data['isc_35'] / data['dii']
data['isc_si/dii'] = data['isc_si'] / data['dii']

location = pvlib.location.Location(latitude=40.4, longitude=-3.7, altitude=695, tz='Europe/Madrid')

solar_zenith = location.get_solarposition(data.index).zenith
solar_azimuth = location.get_solarposition(data.index).azimuth

data['aoi'] = pvlib.irradiance.aoi(surface_tilt=30, surface_azimuth=180,
                                   solar_zenith=solar_zenith, solar_azimuth=solar_azimuth)


data.plot(x='aoi', y='isc35/dii', style='.', ylim=[0, 0.001])
data.plot(x='aoi', y='isc_si/dii', style='.', ylim=[0, 0.01])
