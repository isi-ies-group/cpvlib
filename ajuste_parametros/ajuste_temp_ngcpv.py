# -*- coding: utf-8 -*-
"""
Created on Fri Apr 17 00:20:08 2020

@author: Ruben
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

from pvlib.temperature import sapm_module, pvsyst_cell

def ajuste_temp_sapm_module(data, grafica=True):
    def f(meteo_inputs, a ,b):
        poa_global, temp_air, wind_speed = meteo_inputs
        return sapm_module(poa_global, temp_air, wind_speed, a, b)
    
    (a, b), pcov = curve_fit(f, (data.dni, data.temp_air, data.wind_speed), data.temp_cell_35)
    
    temp_cell_35_est_sapm = sapm_module(data.dni, data.temp_air, data.wind_speed, a, b)
    
    residuals_sapm = data.temp_cell_35 - temp_cell_35_est_sapm
    RMSE_sapm = np.sqrt(((residuals_sapm) ** 2).mean())
    print('RMSE SAPM_module:', RMSE_sapm)
    
    if grafica:
        plt.figure()
        plt.hist2d(data.temp_cell_35, temp_cell_35_est_sapm, bins=30)
        plt.grid(True)
        
        plt.figure()
        plt.hist(residuals_sapm, bins=100)
    
    return a, b

def ajuste_temp_pvsyst_cell(data, grafica=True):
    def f(meteo_inputs, u_c, u_v, eta_m, alpha_absorption):
        poa_global, temp_air, wind_speed = meteo_inputs
        return pvsyst_cell(poa_global, temp_air, wind_speed, u_c, u_v, eta_m, alpha_absorption)
    
    (u_c, u_v, eta_m, alpha_absorption), pcov = curve_fit(f, (data.dni, data.temp_air, data.wind_speed), data.temp_cell_35)
    
    temp_cell_35_est_pvsyst = pvsyst_cell(data.dni, data.temp_air, data.wind_speed, u_c, u_v, eta_m, alpha_absorption)
    
    residuals_pvsyst = data.temp_cell_35 - temp_cell_35_est_pvsyst
    RMSE_pvsyst = np.sqrt(((residuals_pvsyst) ** 2).mean())
    print('RMSE PVSyst_cell:', RMSE_pvsyst)
    
    if grafica:
        plt.figure()
        plt.hist2d(data.temp_cell_35, temp_cell_35_est_pvsyst, bins=30)
        plt.grid(True)
        
        plt.figure()
        plt.hist(residuals_pvsyst, bins=100)
    
    return u_c, u_v, eta_m, alpha_absorption

def lee_fichero_query_pd(fichero_filtro):
    with open(fichero_filtro) as f:
        filtro = f.read()
    
    return filtro

#%% vdf
data_vdf = pd.read_csv('../datos/2012-12_2014-04_fadriquePlant.zip',
                      index_col='timedate', parse_dates=True).resample('T').mean()

data_vdf = data_vdf.query(lee_fichero_query_pd('../datos/filtro_vdf.txt'))

data_vdf = data_vdf.rename(columns={
    'B': 'dni',
    'tamb': 'temp_air',
    'v_viento': 'wind_speed',
    'tmod': 'temp_cell_35',
})

data_vdf = data_vdf[['dni', 'temp_air', 'wind_speed', 'temp_cell_35']].dropna()

print("a, b =", ajuste_temp_sapm_module(data_vdf))
print("u_c, u_v, eta_m, alpha_absorption =", ajuste_temp_pvsyst_cell(data_vdf, grafica=False))

#%% intrepid
data_int = pd.read_csv('../datos/2014-05_2015-05_intrepidTracker.zip',
                      index_col='datetime', parse_dates=True)

data_int = data_int.query(lee_fichero_query_pd('../datos/filtro_intrepid.txt'))

data_int = data_int.rename(columns={
    'B': 'dni',
    'tamb': 'temp_air',
    'v_viento': 'wind_speed',
    'termopar_3': 'temp_cell_35',
})

data_int = data_int[['dni', 'temp_air', 'wind_speed', 'temp_cell_35']].dropna()
data_int = data_int.query('temp_cell_35 > -10')

print("a, b =", ajuste_temp_sapm_module(data_int))
print("u_c, u_v, eta_m, alpha_absorption =", ajuste_temp_pvsyst_cell(data_int, grafica=False))
