# -*- coding: utf-8 -*-
"""
Created on Tue Mar  3 19:09:17 2020
@author: Ruben
"""

import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt

import pvlib
import cpvsystem as cpvlib

module_params_cpv = {
    "gamma_ref": 5.524,
    "mu_gamma": 0.003,
    "I_L_ref": 0.96,
    "I_o_ref": 0.00000000017,
    "R_sh_ref": 5226,
    "R_sh_0": 21000,
    "R_sh_exp": 5.50,
    "R_s": 0.01,
    "alpha_sc": 0.00,
    "EgRef": 3.91,
    "irrad_ref": 1000,
    "temp_ref": 25,
    "cells_in_series": 12,
    "cells_in_parallel": 48,
    "eta_m": 0.32,
    "alpha_absorption": 0.9,
    # "Area": 1.2688,
    # "Impo": 8.3,
    # "Vmpo": 43.9,
}

UF_parameters_cpv = {
    "IscDNI_top": 0.96 / 1000,
    "am_thld": 4.574231933073185,
    "am_uf_m_low": 3.906372068620377e-06,
    "am_uf_m_high": -3.0335768119184845e-05,
    "ta_thld": 50,
    "ta_uf_m_low": 4.6781224141650075e-06,
    "ta_uf_m_high": 0,
    "weight_am": 0.2,
    "weight_temp": 0.8,
}

module_params_cpv.update(UF_parameters_cpv)

# data = pd.read_csv('data2020_03_14.txt', sep='\t', index_col='yyyy/mm/dd hh:mm', parse_dates=True)

data = pd.read_csv('InsolightMay2019.csv', index_col='Date Time',
                   parse_dates=True, encoding='latin1')
data.index = data.index.tz_localize('Europe/Madrid')

data = data.rename(columns={
    'DNI (W/m2)': 'dni',
    'DII (W/m2)': 'dii',
    'GII (W/m2)': 'gii',
    'T_Amb (°C)': 'temp_air',
    'Wind Speed (m/s)': 'wind_speed',
    'T_Backplane (°C)': 'temp_cell',
    'ISC_measured_IIIV (A)':'isc35',
    'ISC_measured_Si (A)':'iscSi',
})

# GII (W/m2): The Global Inclined (plane of array) Irradiance is calculated by
# first calculating the DII(41°), that is the DII corresponding to the G(41°) measurement,
# and finding the Diffuse Inclined Irradiance Diff(41°) = G(41°) – DII(41°). It is
# assumed that the Diffuse Inclined Irradiance at 41° and 30° is equal, so GII = DII + Diff(41°).

location = pvlib.location.Location(
    latitude=40.4, longitude=-3.7, altitude=695, tz='Europe/Madrid')

solar_zenith = location.get_solarposition(data.index).zenith
solar_azimuth = location.get_solarposition(data.index).azimuth

# en fichero 'data2020_03_14.txt', el pira de difusa está sin bola sombreado (comparación piras)
# data['Dh'] = data['Gh'] - (data['Bn'] * np.cos(np.radians(solar_zenith)))

# %% StaticCPVSystem
static_cpv_sys = cpvlib.StaticCPVSystem(
    surface_tilt=30,
    surface_azimuth=180,
    module=None,
    module_parameters=module_params_cpv,
    modules_per_string=1,
    strings_per_inverter=1,
    inverter=None,
    inverter_parameters=None,
    racking_model="insulated",
    losses_parameters=None,
    name=None,
)

data['aoi'] = static_cpv_sys.get_aoi(solar_zenith, solar_azimuth)

data['dii_effective'] = data['dii'] * pvlib.iam.ashrae(data['aoi'], b=0.7)

diode_parameters_cpv = static_cpv_sys.calcparams_pvsyst(
    data['dii_effective'], data['temp_cell'])

dc_cpv = static_cpv_sys.singlediode(*diode_parameters_cpv)

airmass_absolute = location.get_airmass(data.index).airmass_absolute

# OJO uf_global NO incluye uf_aoi!!
uf_global = static_cpv_sys.get_global_utilization_factor(airmass_absolute, data['temp_air'],
                                                        solar_zenith, solar_azimuth)

#%% Plot Isc - CPV
# data['isc35'].plot()
# (dc_cpv['i_sc'] * uf_global).plot()

# %% StaticDiffuseSystem
# toma valores por defecto de module_params_diffuse para método calcparams_pvsyst() en:
# https://github.com/pvlib/pvlib-python/blob/e526b55365ab0f4c473b40b24ae8a82c7e42f892/pvlib/tests/conftest.py#L171-L191
module_params_diffuse = {
    "gamma_ref": 1.05, # valor de test de calcparams_pvsyst() 
    "mu_gamma": 0.001, # valor de test de calcparams_pvsyst() 
    "I_L_ref": 6.0, # valor de test de calcparams_pvsyst() 
    "I_o_ref": 5e-9, # valor de test de calcparams_pvsyst() 
    "R_sh_ref": 300, # valor de test de calcparams_pvsyst() 
    "R_sh_0": 1000, # valor de test de calcparams_pvsyst() 
    "R_sh_exp": 5.5, # valor de test de calcparams_pvsyst() 
    "R_s": 0.5, # valor de test de calcparams_pvsyst() 
    "alpha_sc": 0.001, # valor de test de calcparams_pvsyst() 
    "EgRef": 1.121, # valor de test de calcparams_pvsyst() 
    "irrad_ref": 1000, # calcparams_pvsyst()
    "temp_ref": 25, # calcparams_pvsyst()
    "cells_in_series": 12, # calcparams_pvsyst()
    "cells_in_parallel": 48,
    "eta_m": 0.1, # valor por defecto de pvsyst_celltemp()
    "alpha_absorption": 0.9, # valor por defecto de pvsyst_celltemp()
    # "Area": 1.2688,
    # "Impo": 8.3, # parámetro de sapm()
    # "Vmpo": 43.9, # parámetro de sapm()
}

static_diffuse_sys = cpvlib.StaticDiffuseSystem(
    surface_tilt=30,
    surface_azimuth=180,
    module=None,
    module_parameters=module_params_diffuse,
    modules_per_string=1,
    strings_per_inverter=1,
    inverter=None,
    inverter_parameters=None,
    racking_model="insulated",
    losses_parameters=None,
    name=None,
)

# el aoi de difusa es el mismo que cpv
data['poa_diffuse_static'] = static_diffuse_sys.get_irradiance(solar_zenith,
                                                               solar_azimuth,
                                                               aoi=data['aoi'],
                                                               aoi_limit=55,
                                                               dii=data['dii'], # dii_effective no aplica, ya que si no el calculo de difusa es artificialmente alto!
                                                               gii=data['gii']
                                                               )

celltemp_diffuse = static_diffuse_sys.pvsyst_celltemp(
    data['poa_diffuse_static'], data['temp_air'], data['wind_speed']
)

diode_parameters_diffuse = static_diffuse_sys.calcparams_pvsyst(
    data['poa_diffuse_static'], celltemp_diffuse)

dc_diffuse = static_diffuse_sys.singlediode(*diode_parameters_diffuse)

#%% Plot Isc - diffuse
# data['iscSi'].plot()
# dc_diffuse['i_sc'].plot()

# %% Irradiancias
# data[['dni', 'dii', 'dii_effective', 'gii', 'poa_diffuse_static']].plot(legend=True)

#%% StaticHybridSystem
static_hybrid_sys = cpvlib.StaticHybridSystem(
    surface_tilt=30,
    surface_azimuth=180,
    module_cpv=None,
    module_diffse=None,
    module_params_cpv=module_params_cpv,
    module_parameters_diffuse=module_params_diffuse,
    modules_per_string=1,
    strings_per_inverter=1,
    inverter=None,
    inverter_parameters=None,
    racking_model="insulated",
    losses_parameters=None,
    name=None,
    )

dii_h, poa_diffuse_static_h = static_hybrid_sys.get_irradiance(solar_zenith,
                                solar_azimuth,
                                aoi=data['aoi'],
                                aoi_limit=55,
                                dii=data['dii'], # dii_effective no aplica, ya que si no el calculo de difusa es artificialmente alto!
                                gii=data['gii']
                                )
