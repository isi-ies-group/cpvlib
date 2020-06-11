# -*- coding: utf-8 -*-
"""
Created on Thu Jun 11 02:34:24 2020

@author: Ruben
"""
import pandas as pd
import matplotlib.pyplot as plt
import pvlib

import cpvlib
from insolight_parameters import mod_params_cpv, mod_params_flatplate

lat, lon = 40.4, -3.7

data = pd.read_csv('data/InsolightMay2019.csv', index_col='Date Time',
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
    'PMP_estimated_IIIV (W)': 'pmp35',
    'PMP_estimated_Si (W)': 'pmpSi'
})

# GII (W/m2): The Global Inclined (plane of array) Irradiance is calculated by
# first calculating the DII(41°), that is the DII corresponding to the G(41°) measurement,
# and finding the Diffuse Inclined Irradiance Diff(41°) = G(41°) – DII(41°). It is
# assumed that the Diffuse Inclined Irradiance at 41° and 30° is equal, so GII = DII + Diff(41°).

location = pvlib.location.Location(
    latitude=lat, longitude=lon, altitude=695, tz='utc')

solar_zenith = location.get_solarposition(data.index).zenith
solar_azimuth = location.get_solarposition(data.index).azimuth

#%%
# StaticHybridSystem
static_hybrid_sys = cpvlib.StaticHybridSystem(
    surface_tilt=30,
    surface_azimuth=180,
    module_cpv=None,
    module_flatplate=None,
    module_parameters_cpv=mod_params_cpv,
    module_parameters_flatplate=mod_params_flatplate,
    modules_per_string=1,
    strings_per_inverter=1,
    inverter=None,
    inverter_parameters=None,
    racking_model="insulated",
    losses_parameters=None,
    name=None,
)

# get_effective_irradiance
theta_ref = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]
iam_ref = [1.000, 1.007, 0.998, 0.991, 0.971, 0.966, 0.938, 0.894, 0.830, 0.790, 0.740, 0.649, 0.387]

data['dii_effective'], data['poa_flatplate_static_effective'] = static_hybrid_sys.get_effective_irradiance(
    solar_zenith,
    solar_azimuth,
    theta_ref,
    iam_ref,
    # iam_param=0.7,
    aoi_limit=55,
    dii=None,
    gii=data['gii'],
    dni=data['dni'],
    spillage=0.23
)
aoi = static_hybrid_sys.static_cpv_sys.get_aoi(solar_zenith, solar_azimuth)
data['poa_flatplate_static_effective'] *= pvlib.iam.interp(aoi, [0, 30, 60], [0.5, 1, 1], method='linear', normalize=False)
 
# pvsyst_celltemp
data['temp_cell_35'], data['temp_cell_flatplate'] = static_hybrid_sys.pvsyst_celltemp(
    dii=data['dii_effective'],
    poa_flatplate_static=data['poa_flatplate_static_effective'],
    temp_air=data['temp_air'],
    wind_speed=data['wind_speed']
)

# calcparams_pvsyst
diode_parameters_cpv, diode_parameters_flatplate = static_hybrid_sys.calcparams_pvsyst(
    dii=data['dii_effective'],
    poa_flatplate_static=data['poa_flatplate_static_effective'],
    temp_cell_cpv=data['temp_cell_35'],
    temp_cell_flatplate=data['temp_cell_flatplate'],
)

# singlediode
dc_cpv, dc_flatplate = static_hybrid_sys.singlediode(
    diode_parameters_cpv, diode_parameters_flatplate)

# uf_global (uf_am, uf_temp_air)
data['am'] = location.get_airmass(data.index).airmass_absolute

uf_cpv = static_hybrid_sys.get_global_utilization_factor_cpv(data['am'], data['temp_air'])

#%% Plot Isc - CPV
# data['isc35'].plot()
# (dc_cpv['i_sc'] * uf_cpv).plot()

#%% Plot Isc - diffuse
fig, axs = plt.subplots(2, sharex=True)
data['iscSi'].plot(ax=axs[0], ylim=[0, 5]); dc_flatplate['i_sc'].plot(ax=axs[0], )
# (aoi/20).plot(ylim=[0, 5])
# (data['poa_flatplate_static_effective']/120).plot(ylim=[0, 5])
#%% Plot Pmp - diffuse
# data['pmpSi'].plot(ylim=[0, 5]); dc_flatplate['p_mp'].plot()

#%% Irradiancias
data[['dni', 'dii', 'dii_effective', 'gii', 'poa_flatplate_static_effective']].plot(ax=axs[1], legend=True)
