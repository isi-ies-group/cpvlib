# -*- coding: utf-8 -*-
"""
Created on Fri May  8 22:49:15 2020

@author: Ruben
"""
from math import sqrt

import matplotlib.pyplot as plt
import pvlib

lat, lon = 40.4, -3.7

data_pvgis = pvlib.iotools.get_pvgis_tmy(lat, lon)

data_tmy = data_pvgis[0].rename(columns={
    'Gb(n)': 'dni',
    'G(h)': 'ghi',
    'Gd(h)': 'dhi',
    'T2m': 'temp_air',
    'WS10m': 'wind_speed',
})

data_tmy = data_tmy.set_index(
    data_tmy.index.map(lambda t: t.replace(year=2010)))

data = data_tmy#['2010-06-01':'2010-06-01']

location = pvlib.location.Location(
    latitude=lat, longitude=lon, altitude=695, tz='utc')

solpos = location.get_solarposition(data.index)

# %% Parámetros
# R_sh_exp = 5.5, # exp. R paral VALOR_DEFECTO
# EgRef = 1.121, # VALOR_DEFECTO
# irrad_ref = 1000,
# temp_ref = 25

A_ref = 10

modulo = 'isofoton'

if modulo == 'ejemplo':
    # https://pvpmc.sandia.gov/PVLIB_Matlab_Help/html/pvl_calcparams_PVsyst_help.html
    A = 1  # m2
    
    corr = A_ref / A
    A *= corr
    pv_mod_params = {
        "alpha_sc": -0.002,# coef. temp. Isc
        "gamma_ref": 1.1,# "Datos básicos"
        "mu_gamma": -0.0003,# "Parámetros modelo"
        "I_L_ref": 5.5 *sqrt(corr),# Isc
        "I_o_ref": 2.2e-9,# "Datos básicos"
        "R_sh_ref": 200, # R paral ref "Parámetros modelo"
        "R_sh_0": 8700,# R paral G=0 W/m2 "Parámetros modelo"
        "R_s": 0.33,# R serie "Parámetros modelo"
        "cells_in_series": 60 *sqrt(corr),
    }
        
elif modulo == 'isofoton':
    # Isofoton_I110 - PVSyst
    A = 0.85  # m2

    corr = A_ref / A
    A *= corr
    pv_mod_params = {
        "alpha_sc": 2.3e-3,  # coef. temp. Isc
        "gamma_ref": 0.970,  # "Datos básicos"
        "mu_gamma": 0,  # "Parámetros modelo"
        "I_L_ref": 6.76 *sqrt(corr),#*sqrt(10/0.85),  # Isc
        "I_o_ref": 0.23e-9,  # "Datos básicos"
        "R_sh_ref": 200,  # R paral ref "Parámetros modelo"
        "R_sh_0": 800,  # R paral G=0 W/m2 "Parámetros modelo"
        "R_s": 0.248,  # R serie "Parámetros modelo"
        "cells_in_series": 36 *sqrt(corr),# *sqrt(10/0.85),
    }

#%%
# calcula Pmp STC
Pdc_stc = pvlib.pvsystem.singlediode(*pvlib.pvsystem.PVSystem(
    module_parameters=pv_mod_params
    ).calcparams_pvsyst(
    effective_irradiance=1000,
    temp_cell=25))['p_mp']

eff_a = Pdc_stc / (1000 * A)

temp_mod_params = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['pvsyst']['freestanding']
# print(temp_mod_params)

#%% Modelo PVSyst
pv_sys = pvlib.pvsystem.PVSystem(
    surface_tilt=37,
    surface_azimuth=180,
    # albedo=0.2,
    module_parameters=pv_mod_params,
    temperature_model_parameters=temp_mod_params,
    modules_per_string=1,
)

pv_irr = pv_sys.get_irradiance(
    solar_zenith=solpos['zenith'],
    solar_azimuth=solpos['azimuth'],
    ghi=data['ghi'],
    dhi=data['dhi'],
    dni=data['dni']
)

irradiance = pv_irr['poa_global']
# irradiance.plot();data.ghi.plot()

# AOI
# pv_aoi = pv_sys.get_aoi(
#     solar_zenith=solpos['zenith'],
#     solar_azimuth=solpos['azimuth'],
# )
# pv_aoi.plot()

cell_temp = pv_sys.pvsyst_celltemp(
    poa_global=irradiance,
    temp_air=data['temp_air'],
    wind_speed=data['wind_speed']
)

# MODELO TÉRMICO SANDIA
# temp_mod_params = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']
# print(temp_mod_params)
# cell_temp_sapm = pvlib.temperature.sapm_cell(
#     poa_global=pv_irr['poa_global'],
#     temp_air=data['temp_air'],
#     wind_speed=data['wind_speed'],
#     **temp_mod_params
# )

diode_parameters = pv_sys.calcparams_pvsyst(
    effective_irradiance=irradiance,
    temp_cell=cell_temp,
)

power = pv_sys.singlediode(*diode_parameters)

Yr = irradiance.resample('M').sum() / 1000
Ya = power['p_mp'].resample('M').sum() / Pdc_stc

Lc = Yr - Ya

PR = Ya / Yr

print('Yield PV')
print(f'Pdc_stc={Pdc_stc:.0f} W, eff_a={eff_a:.2%}')
print(f'PR={Ya.sum()/Yr.sum():.2}, Ya={Ya.sum():.0f} kWh/kW, Yr={Yr.sum():.0f} kWh/kW')
print(f'Total TMY energy per reference area={power["p_mp"].sum()/1000:.0f} kWh/year')

#%% Curvas IV vs G,Tc
for G in [200, 400, 600, 800, 1000]:
    d = pv_sys.singlediode(*pv_sys.calcparams_pvsyst(
        effective_irradiance=G,
        temp_cell=25,
        ), ivcurve_pnts=20
        )
    plt.plot(d['v'], d['i'])

for t in [10, 25, 40, 55, 70]:
    d = pv_sys.singlediode(*pv_sys.calcparams_pvsyst(
        effective_irradiance=1000,
        temp_cell=t,
        ), ivcurve_pnts=20
        )
    plt.plot(d['v'], d['i'])

#%% Grafica V_mp vs cell_temp
plt.plot(cell_temp, power['v_mp'], '.')
