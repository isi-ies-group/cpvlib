# -*- coding: utf-8 -*-
"""
Created on Wed Apr  8 17:01:27 2020

@author: Ruben
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

import pvlib

data = pd.read_csv('../datos/InsolightMay2019.csv', index_col='Date Time', parse_dates=True, encoding='latin1')
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


location = pvlib.location.Location(latitude=40.4, longitude=-3.7, altitude=695, tz='Europe/Madrid')

solar_zenith = location.get_solarposition(data.index).zenith
solar_azimuth = location.get_solarposition(data.index).azimuth

data['aoi'] = pvlib.irradiance.aoi(surface_tilt=30, surface_azimuth=180,
                                   solar_zenith=solar_zenith, solar_azimuth=solar_azimuth)

# filtro 3 días soleados
data = data['2019-05-30':'2019-06-01']

data['isc35/dii'] = data['isc_35'] / data['dii']
isc35_dii_max = data['isc35/dii'][data.aoi<55].max()

# Normaliza por el máximo
data['isc35/dii'] /= isc35_dii_max

#%% Plot isc, aoi
data[['isc_35', 'isc_si', 'aoi']].plot(secondary_y='aoi')

#%% ajuste iam.ashrae
data_noinf = data.drop(data[data.dii == 0].index)[data.aoi<55]

param_b,_ = curve_fit(pvlib.iam.ashrae, data_noinf['aoi'], data_noinf['isc35/dii'])

isc35_dii_est_ashrae = pvlib.iam.ashrae(data_noinf['aoi'], b=param_b)

residuals_ashrae = data_noinf['isc35/dii'] - isc35_dii_est_ashrae
RMSE_ashrae = np.sqrt(((residuals_ashrae) ** 2).mean())
print(RMSE_ashrae)
plt.hist(residuals_ashrae, bins=100)

data.plot(x='aoi', y='isc35/dii', style='.', ylim=[0, 1.3])
plt.plot(data_noinf['aoi'], isc35_dii_est_ashrae, label=f"{param_b[0]:.2f}", linewidth=0.5)
plt.legend()
plt.grid()

#%% Plots IAM - Martin Ruiz
data.plot(x='aoi', y='isc35/dii', style='.', ylim=[0, 1.3])
# data.plot(x='aoi', y='isc_si/dii', style='.', ylim=[0, 0.01])

for var in np.arange(start=1, stop=150, step=10):
    plt.plot(data['aoi'], pvlib.iam.martin_ruiz(data['aoi'], a_r=var), label="{0:.2f}".format(var), linewidth=0.5)

plt.legend()

#%% ajuste iam.physical pvlib.iam.physical(aoi, n=1.526, K=4., L=0.002)
(n, K, L),_ = curve_fit(pvlib.iam.physical, data_noinf['aoi'], data_noinf['isc35/dii'])

isc35_dii_est_phys = pvlib.iam.physical(data_noinf['aoi'], n, K, L)

residuals_phys = data_noinf['isc35/dii'] - isc35_dii_est_phys
RMSE_phys = np.sqrt(((residuals_phys) ** 2).mean())
print(RMSE_phys)
plt.hist(residuals_phys, bins=100)

data.plot(x='aoi', y='isc35/dii', style='.', ylim=[0, 1.3])
plt.plot(data_noinf['aoi'], isc35_dii_est_phys, label=f"{n:.2f}, {K:.2f}, {L:.2f}", linewidth=0.5)
plt.legend()
plt.grid()