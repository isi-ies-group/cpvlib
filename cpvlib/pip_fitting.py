# -*- coding: utf-8 -*-
"""
Created on Thu Jun 11 02:34:24 2020

@author: Ruben
"""
import pandas as pd
import numpy as np
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
    'G(41°) (W/m2)': 'g41',
    'DNI_Top (W/m2)': 'top',
    'DNI_Mid (W/m2)': 'mid',
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

data['smr1'] = data.top / data.mid

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
    theta_ref=theta_ref,
    iam_ref=iam_ref,
    # iam_param=0.7,
    aoi_limit=55,
    dii=None,
    gii=data['gii'],
    dni=data['dni'],
    spillage=0.15
)
aoi = static_hybrid_sys.static_cpv_sys.get_aoi(solar_zenith, solar_azimuth)
data['poa_flatplate_static_effective'] *= pvlib.iam.interp(aoi, [0, 30, 50, 75, 90], [0.5, 1, 1, 0.1, 0.01], method='linear', normalize=False)

# data['poa_flatplate_static_effective'] *= pvlib.iam.interp(aoi, [50, 60, 90], [1, 1, 0.1], method='linear', normalize=False)

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
    temp_cell_flatplate=data['temp_cell_35'],
)

# singlediode
dc_cpv, dc_flatplate = static_hybrid_sys.singlediode(
    diode_parameters_cpv, diode_parameters_flatplate)

# uf_global (uf_am, uf_temp_air)
data['am'] = location.get_airmass(data.index).airmass_absolute

uf_cpv = static_hybrid_sys.get_global_utilization_factor_cpv(data['am'], data['temp_air'])

#%% RMSE y R2
dia_ini = '2019-06-01'#'2019-05-31'
dia_fin = '2019-06-02'#'2019-06-01'

def rmse(predictions, targets):
    return np.sqrt(((predictions - targets) ** 2).mean())

rmse_isc35 = rmse(data[dia_ini:dia_fin]['isc35'], dc_cpv[dia_ini:dia_fin]['i_sc'] * uf_cpv[dia_ini:dia_fin])
rmse_iscSi = rmse(data[dia_ini:dia_fin]['iscSi'], dc_flatplate[dia_ini:dia_fin]['i_sc'])

r2_isc35 = np.corrcoef(data[dia_ini:dia_fin]['isc35'], dc_cpv[dia_ini:dia_fin]['i_sc'] * uf_cpv[dia_ini:dia_fin])[0,1]**2
r2_iscSi = np.corrcoef(data[dia_ini:dia_fin]['iscSi'], dc_flatplate[dia_ini:dia_fin]['i_sc'])[0,1]**2

print('r2_isc35:', r2_isc35, 'rmse_isc35', rmse_isc35)
print('r2_iscSi:', r2_iscSi, 'rmse_iscSi:', rmse_iscSi)

#%% Plot Pmp
from matplotlib.gridspec import GridSpec

grid = GridSpec(nrows=2, ncols=3, wspace=0.5, hspace=0.5)
fig = plt.figure()

ax1 = fig.add_subplot(grid[0, 0:2])
ax2 = fig.add_subplot(grid[1, 0:2], sharex=ax1)
ax3 = fig.add_subplot(grid[0, 2], xticks=[0, 10, 20], yticks=[0, 10, 20])
ax4 = fig.add_subplot(grid[1, 2], xticks=[0, 1.5, 3], yticks=[0, 1.5, 3])


# [dc_flatplate['i_sc'] == dc_flatplate[dia_ini:dia_fin]['i_sc'].argmax()] = None

data[dia_ini:dia_fin]['pmp35'].plot(ax=ax1, label='Measurement')
(dc_cpv[dia_ini:dia_fin]['p_mp'] * uf_cpv).plot(ax=ax1, label='Model', color='tab:orange')

data[dia_ini:dia_fin]['pmpSi'].plot(ax=ax2, ylim=[0, 5], label='Measurement')
dc_flatplate[dia_ini:dia_fin]['p_mp'].plot(ax=ax2, label='Model', color='tab:orange')

ax2.set_xlabel('')
ax2.set_ylim([0, 4])
ax1.tick_params(axis='both', which='both', length=0)
ax2.tick_params(axis='both', which='both', length=0)

ax2.yaxis.set_ticks([0, 1.5, 3])
from matplotlib import dates

ax2.xaxis.set_major_locator(dates.HourLocator(byhour=14, interval=1))
ax2.xaxis.set_major_formatter(dates.DateFormatter('%d-%b'))

ax1.set_title('$P_{MP}$ III-V')
ax1.set_ylabel('[W]', rotation=0)
ax1.yaxis.set_label_coords(-0.04, 1.02)
ax1.legend()
ax2.set_title('$P_{MP}$ Si')
ax2.set_ylabel('[W]', rotation=0)
ax2.yaxis.set_label_coords(-0.04, 1.02)
ax2.legend()

# Plot Scatter Pmp
# fig, axs = plt.subplots(2)

ax3.scatter(data[dia_ini:dia_fin]['pmp35'], dc_cpv[dia_ini:dia_fin]['p_mp'] * uf_cpv[dia_ini:dia_fin], c='tab:red', s=2)
ax3.grid(True)
ax3.axis('equal')
ax3.set_xlabel('Measurement')
ax3.set_ylabel('Model')

ax4.scatter(data[dia_ini:dia_fin]['pmpSi'], dc_flatplate[dia_ini:dia_fin]['p_mp'], c='tab:red', s=2)
ax4.grid(True)
ax4.axis('equal')
ax4.set_xlabel('Measurement')
ax4.set_ylabel('Model')

from pathlib import Path
fig.savefig(Path.home() / 'Desktop/PiP_fitting_pmp_2dias.png', dpi=600, bbox_inches='tight')

#%% Plot Isc
from matplotlib.gridspec import GridSpec

grid = GridSpec(nrows=2, ncols=3, wspace=0.5, hspace=0.5)
fig = plt.figure()

ax1 = fig.add_subplot(grid[0, 0:2])
ax2 = fig.add_subplot(grid[1, 0:2], sharex=ax1)
ax3 = fig.add_subplot(grid[0, 2], xticks=[0, 0.25, 0.5, 0.75], yticks=[0, 0.25, 0.5, 0.75])
ax4 = fig.add_subplot(grid[1, 2], xticks=[0, 1, 2, 3], yticks=[0, 1, 2, 3])


# [dc_flatplate['i_sc'] == dc_flatplate[dia_ini:dia_fin]['i_sc'].argmax()] = None

data[dia_ini:dia_fin]['isc35'].plot(ax=ax1, label='Measurement')
(dc_cpv[dia_ini:dia_fin]['i_sc'] * uf_cpv).plot(ax=ax1, label='Model', color='tab:orange')

data[dia_ini:dia_fin]['iscSi'].plot(ax=ax2, ylim=[0, 5], label='Measurement')
dc_flatplate[dia_ini:dia_fin]['i_sc'].plot(ax=ax2, label='Model', color='tab:orange')

ax2.set_xlabel('')
ax2.set_ylim([0, 4])
ax1.tick_params(axis='both', which='both', length=0)
ax2.tick_params(axis='both', which='both', length=0)

ax1.set_title('$I_{SC}$ III-V [A]')
ax1.legend()
ax2.set_title('$I_{SC}$ Si [A]')
ax2.legend()

# Plot Scatter Pmp
# fig, axs = plt.subplots(2)

ax3.scatter(data[dia_ini:dia_fin]['isc35'], dc_cpv[dia_ini:dia_fin]['i_sc'] * uf_cpv[dia_ini:dia_fin], c='tab:red', s=2)
ax3.grid(True)
ax3.axis('equal')
ax3.set_xlabel('Measurement')
ax3.set_ylabel('Model')

ax4.scatter(data[dia_ini:dia_fin]['iscSi'], dc_flatplate[dia_ini:dia_fin]['i_sc'], c='tab:red', s=2)
ax4.grid(True)
ax4.axis('equal')
ax4.set_xlabel('Measurement')
ax4.set_ylabel('Model')

#%% Irradiancias
# data['2019-05-31'][['dni', 'dii', 'dii_effective', 'gii', 'poa_flatplate_static_effective']].plot(legend=True)
dia = '2019-05-31'

fig, [ax1, cax] = plt.subplots(1,2, gridspec_kw=dict(width_ratios=[10,1], wspace=0.1))
img = ax1.scatter(solar_zenith[dia], data[dia]['g41'], c=data[dia].temp_air)

cbar = plt.colorbar(img, ax=ax1, cax=cax)
cbar.set_label('Air temp. [ºC]')
plt.title('G(41) vs Zenith angle')

ax2 = ax1.twinx()
ax2.scatter(solar_zenith[dia], data[dia]['smr1'], c=data[dia].temp_air)
