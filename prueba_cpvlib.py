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
    "Area": 1.2688,
    "Impo": 8.3,
    "Vmpo": 43.9,
}

UF_parameters_cpv = {
    "IscDNI_top": 0.96 / 1000,
    "aoi_thld": 61.978505569631494,
    "aoi_uf_m_low": -2.716773886925838e-07,
    "aoi_uf_m_high": -1.781998474992582e-05,
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

data = pd.read_csv('InsolightMay2019.csv', index_col='Date Time', parse_dates=True, encoding='latin1')
data.index = data.index.tz_localize('Europe/Madrid')

data = data.rename(columns={
    'DNI (W/m2)':'dni',
    'DII (W/m2)':'dii',
    'GII (W/m2)':'gii',
    'T_Amb (°C)':'temp_air',
    'Wind Speed (m/s)':'wind_speed',
    'T_Backplane (°C)':'temp_cell',
    })

# GII (W/m2): The Global Inclined (plane of array) Irradiance is calculated by 
# first calculating the DII(41°), that is the DII corresponding to the G(41°) measurement, 
# and finding the Diffuse Inclined Irradiance Diff(41°) = G(41°) – DII(41°). It is 
# assumed that the Diffuse Inclined Irradiance at 41° and 30° is equal, so GII = DII + Diff(41°).

location = pvlib.location.Location(latitude=40.4, longitude=-3.7, altitude=695, tz='Europe/Madrid')

solar_zenith = location.get_solarposition(data.index).zenith
solar_azimuth = location.get_solarposition(data.index).azimuth

# en fichero 'data2020_03_14.txt', el pira de difusa está sin bola sombreado (comparación piras)
# data['Dh'] = data['Gh'] - (data['Bn'] * np.cos(np.radians(solar_zenith)))

#%% StaticCPVSystem
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

# data['dii'] = static_cpv_sys.get_irradiance(solar_zenith, solar_azimuth, data['dni'])

# temp_cell = static_cpv_sys.pvsyst_celltemp(
#     data['dii'], data[temp_air'], data['wind_speed']
# )

diode_parameters_cpv = static_cpv_sys.calcparams_pvsyst(
    data['dii'], data['temp_cell'])
   
dc_cpv = static_cpv_sys.singlediode(*diode_parameters_cpv)

# TO DO: Ejecutar los UFs internamente en StaticCPVSystem
uf_am = static_cpv_sys.get_am_util_factor(airmass=
                                          location.get_airmass(data.index).airmass_absolute)

uf_ta = static_cpv_sys.get_tempair_util_factor(temp_air=data['temp_air'])

uf_am_at = uf_am * module_params_cpv['weight_am'] + uf_ta * module_params_cpv['weight_temp']

aoi = static_cpv_sys.get_aoi(solar_zenith, solar_azimuth)

uf_aoi = static_cpv_sys.get_aoi_util_factor(aoi=aoi)

uf_aoi_ast = static_cpv_sys.get_aoi_util_factor(aoi=0)

uf_aoi_norm = uf_aoi / uf_aoi_ast

uf_global = uf_am_at * uf_aoi_norm
# TO DO

(dc_cpv['p_mp'] * uf_global).plot()

#%% DiffuseHybridSystem
module_params_diffuse = {
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
    "Area": 1.2688,
    "Impo": 8.3,
    "Vmpo": 43.9,
}

diffuse_hybrid_sys = cpvlib.DiffuseHybridSystem(
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

# el aoi de hybrid debe ser el mismo que cpv
# aoi = diffuse_hybrid_sys.get_aoi(solar_zenith, solar_azimuth)

data['poa_diffuse_static'] = diffuse_hybrid_sys.get_irradiance(solar_zenith, 
                                                            solar_azimuth,
                                                            aoi=aoi,
                                                            aoi_limit=55,
                                                            dii=data['dii'],
                                                            gii=data['gii']
                                                            )

celltemp_diffuse = diffuse_hybrid_sys.pvsyst_celltemp(
    data['poa_diffuse_static'], data['temp_air'], data['wind_speed']
)

diode_parameters_diffuse = diffuse_hybrid_sys.calcparams_pvsyst(
    data['poa_diffuse_static'], celltemp_diffuse)

dc_diffuse = diffuse_hybrid_sys.singlediode(*diode_parameters_diffuse)

dc_diffuse['p_mp'].plot()

#%% Irradiancias
data[['dni', 'dii', 'gii', 'poa_diffuse_static']].plot()
