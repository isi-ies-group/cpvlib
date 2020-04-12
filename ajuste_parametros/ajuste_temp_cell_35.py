# -*- coding: utf-8 -*-
"""
Created on Wed Apr  8 16:01:01 2020

@author: Ruben
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

from pvlib.temperature import sapm_module, pvsyst_cell

#%% lee datos campaña 2019-05
data = pd.read_csv('../datos/InsolightMay2019.csv', index_col='Date Time',
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

# filtro 3 días soleados
data = data['2019-05-30':'2019-06-01']

#%% Ajuste sapm_module
def f(meteo_inputs, a ,b):
    poa_global, temp_air, wind_speed = meteo_inputs
    return sapm_module(poa_global, temp_air, wind_speed, a, b)

(a, b), pcov = curve_fit(f, (data.dii, data.temp_air, data.wind_speed), data.temp_cell_35)

temp_cell_35_est = sapm_module(data.dii, data.temp_air, data.wind_speed, a, b)

plt.hist2d(data.temp_cell_35, temp_cell_35_est, bins=30)
plt.grid(True)


residuals = data.temp_cell_35 - temp_cell_35_est
RMSE = np.sqrt(((residuals) ** 2).mean())
print(RMSE)
plt.hist(residuals, bins=100)

#%% Ajuste pvsyst_cell
def f(meteo_inputs, u_c, u_v, eta_m=0.1, alpha_absorption=0.9):
    poa_global, temp_air, wind_speed = meteo_inputs
    return pvsyst_cell(poa_global, temp_air, wind_speed, u_c, u_v, eta_m, alpha_absorption)

(u_c, u_v, eta_m, alpha_absorption), pcov = curve_fit(f, (data.dii, data.temp_air, data.wind_speed), data.temp_cell_35)

temp_cell_35_est = pvsyst_cell(data.dii, data.temp_air, data.wind_speed, u_c, u_v, eta_m, alpha_absorption)

plt.hist2d(data.temp_cell_35, temp_cell_35_est, bins=30)
plt.grid(True)


residuals = data.temp_cell_35 - temp_cell_35_est
RMSE = np.sqrt(((residuals) ** 2).mean())
print(RMSE)
plt.hist(residuals, bins=100)