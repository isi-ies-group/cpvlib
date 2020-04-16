# -*- coding: utf-8 -*-
"""
Created on Tue Mar 31 03:04:44 2020

@author: Ruben
"""
import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt

import pvlib
import cpvlib

#%% Parámetros configuración módulo
# https://doi.org/10.5281/zenodo.3346823
# 0.1 m2, 572 micro-cells + 4x 6"(15.24 cm) Si-cells in series
# https://doi.org/10.5281/zenodo.3349781
# 35 rango IV: 0.7 A, 35 V @DNI 900 W/m2
# Si rango IV: 1.7 A, 2.2 V @GNI 950 W/m2 y DNI/GNI=0.7

mod_params_cpv = {
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

mod_params_cpv.update(UF_parameters_cpv)

# toma valores por defecto de mod_params_diffuse para método calcparams_pvsyst() en:
# https://github.com/pvlib/pvlib-python/blob/e526b55365ab0f4c473b40b24ae8a82c7e42f892/pvlib/tests/conftest.py#L171-L191
mod_params_diffuse = {
    "gamma_ref": 1.05,  # valor de test de calcparams_pvsyst()
    "mu_gamma": 0.001,  # valor de test de calcparams_pvsyst()
    "I_L_ref": 4*6.0,  # valor de test de calcparams_pvsyst()
    "I_o_ref": 5e-9,  # valor de test de calcparams_pvsyst()
    "R_sh_ref": 300,  # valor de test de calcparams_pvsyst()
    "R_sh_0": 1000,  # valor de test de calcparams_pvsyst()
    "R_sh_exp": 5.5,  # valor de test de calcparams_pvsyst()
    "R_s": 0.5,  # valor de test de calcparams_pvsyst()
    "alpha_sc": 0.001,  # valor de test de calcparams_pvsyst()
    "EgRef": 1.121,  # valor de test de calcparams_pvsyst()
    "irrad_ref": 1000,  # calcparams_pvsyst()
    "temp_ref": 25,  # calcparams_pvsyst()
    "cells_in_series": 2,  # visto Vmp~=Pmp/Isc
    # "cells_in_parallel": 48, # 
    "eta_m": 0.1,  # valor por defecto de pvsyst_celltemp()
    "alpha_absorption": 0.9,  # valor por defecto de pvsyst_celltemp()
    # "Area": 1.2688,
    # "Impo": 8.3, # parámetro de sapm()
    # "Vmpo": 43.9, # parámetro de sapm()
}

#%% lee datos campaña 2019-05 https://doi.org/10.5281/zenodo.3346822
data = pd.read_csv('datos/InsolightMay2019.csv', index_col='Date Time',
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

location = pvlib.location.Location(
    latitude=40.4, longitude=-3.7, altitude=695, tz='Europe/Madrid')

solar_zenith = location.get_solarposition(data.index).zenith
solar_azimuth = location.get_solarposition(data.index).azimuth

#%% StaticHybridSystem
static_hybrid_sys = cpvlib.StaticHybridSystem(
    surface_tilt=30,
    surface_azimuth=180,
    module_cpv=None,
    module_diffuse=None,
    module_parameters_cpv=mod_params_cpv,
    module_parameters_diffuse=mod_params_diffuse,
    modules_per_string=1,
    strings_per_inverter=1,
    inverter=None,
    inverter_parameters=None,
    racking_model="insulated",
    losses_parameters=None,
    name=None,
)

# get_effective_irradiance
data['dii_effective'], data['poa_diffuse_static'] = static_hybrid_sys.get_effective_irradiance(
    solar_zenith,
    solar_azimuth,
    iam_param=0.7,
    aoi_limit=55,
    dii=None,  # dii_effective no aplica, ya que si no el calculo de difusa es artificialmente alto!
    gii=data['gii'],
    dni=data['dni']
)

# pvsyst_celltemp
_, data['celltemp_diffuse'] = static_hybrid_sys.pvsyst_celltemp(
    dii=data['dii_effective'],
    poa_diffuse_static=data['poa_diffuse_static'],
    temp_air=data['temp_air'],
    wind_speed=data['wind_speed']
)

# calcparams_pvsyst
diode_parameters_cpv, diode_parameters_diffuse = static_hybrid_sys.calcparams_pvsyst(
    dii=data['dii_effective'],
    poa_diffuse_static=data['poa_diffuse_static'],
    temp_cell_cpv=data['temp_cell_35'],
    temp_cell_diffuse=data['celltemp_diffuse'],
)

# singlediode
dc_cpv, dc_diffuse = static_hybrid_sys.singlediode(
    diode_parameters_cpv, diode_parameters_diffuse)

# uf_global
airmass_absolute = location.get_airmass(data.index).airmass_absolute

uf_global = static_hybrid_sys.get_global_utilization_factor_cpv(airmass_absolute, data['temp_air'],
                                                                  solar_zenith, solar_azimuth)
#%% Plot Irradiancias
# data[['dni', 'dii', 'dii_effective', 'gii', 'poa_diffuse_static']].plot(legend=True)

#%% Plot Isc - CPV
# data['isc35'].plot()
# (dc_cpv['i_sc'] * uf_global).plot()

#%% Plot Isc - diffuse
data['iscSi'].plot()
dc_diffuse['i_sc'].plot()

