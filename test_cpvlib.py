# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 18:18:09 2020

@author: Ruben
"""
import pandas as pd

import pvlib
import cpvsystem as cpvlib

module_params = {
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

UF_parameters = {
    "IscDNI_top": 0.96 / 1000,
    "thld_aoi": 61.978505569631494,
    "m_low_aoi": -2.716773886925838e-07,
    "m_high_aoi": -1.781998474992582e-05,
    "thld_am": 4.574231933073185,
    "m_low_am": 3.906372068620377e-06,
    "m_high_am": -3.0335768119184845e-05,
    "thld_temp": 50,
    "m_low_temp": 4.6781224141650075e-06,
    "m_high_temp": 0,
    "weight_am": 0.2,
    "weight_temp": 0.8,
}

module_params.update(UF_parameters)

def test_pmp():
    
    meteo = pd.read_csv('meteo2020_03_04.txt', sep='\t', index_col='yyyy/mm/dd hh:mm', parse_dates=True)
    meteo.index = meteo.index.tz_localize('Europe/Madrid')
    
    location = pvlib.location.Location(latitude=40.4, longitude=-3.7, altitude=695, tz='Europe/Madrid')
    
    static_cpv_sys = cpvlib.StaticCPVSystem(
        surface_tilt=30,
        surface_azimuth=180,
        module=None,
        module_parameters=module_params,
        modules_per_string=1,
        strings_per_inverter=1,
        inverter=None,
        inverter_parameters=None,
        racking_model="insulated",
        losses_parameters=None,
        name=None,
    )
    
    aoi = pvlib.irradiance.aoi(
        static_cpv_sys.surface_tilt,
        static_cpv_sys.surface_azimuth,
        solar_zenith=location.get_solarposition(meteo.index).zenith,
        solar_azimuth=location.get_solarposition(meteo.index).azimuth,
        )
    
    meteo['dii'] = pvlib.irradiance.beam_component(
        static_cpv_sys.surface_tilt,
        static_cpv_sys.surface_azimuth,
        solar_zenith=location.get_solarposition(meteo.index).zenith,
        solar_azimuth=location.get_solarposition(meteo.index).azimuth,
        dni=meteo['Bn']
        )
    
    celltemp = static_cpv_sys.pvsyst_celltemp(
        meteo['dii'], meteo['Temp. Ai 1'], meteo['V.Vien.1']
    )
    
    diode_parameters = static_cpv_sys.calcparams_pvsyst(
        meteo['dii'], celltemp)
       
    dc = static_cpv_sys.singlediode(*diode_parameters)
    
    uf_am = static_cpv_sys.get_am_util_factor(
        airmass=location.get_airmass(meteo.index).airmass_absolute,
        am_thld=module_params['thld_am'], 
        am_uf_m_low=module_params['m_low_am']/module_params['IscDNI_top'],
        am_uf_m_high=module_params['m_high_am']/module_params['IscDNI_top']
        )
    
    uf_ta = static_cpv_sys.get_tempair_util_factor(
    temp_air=meteo['Temp. Ai 1'],
    ta_thld=module_params['thld_temp'] , 
    ta_uf_m_low=module_params['m_low_temp']/module_params['IscDNI_top'],
    ta_uf_m_high=module_params['m_high_temp']/module_params['IscDNI_top']
    )
    
    uf_am_at = uf_am * module_params['weight_am'] + uf_ta * module_params['weight_temp']
    
    # ax=meteo['dii'].plot();meteo['Bn'].plot(ax=ax)
    
    uf_aoi = static_cpv_sys.get_aoi_util_factor(
        aoi=static_cpv_sys.get_aoi(
                solar_zenith=location.get_solarposition(meteo.index).zenith,
                solar_azimuth=location.get_solarposition(meteo.index).azimuth,
                ),
        aoi_thld=module_params['thld_aoi'], 
        aoi_uf_m_low=module_params['m_low_aoi']/module_params['IscDNI_top'],
        aoi_uf_m_high=module_params['m_high_aoi']/module_params['IscDNI_top']
    )
    
    uf_aoi_ast = static_cpv_sys.get_aoi_util_factor(
        aoi=0,
        aoi_thld=module_params['thld_aoi'], 
        aoi_uf_m_low=module_params['m_low_aoi']/module_params['IscDNI_top'],
        aoi_uf_m_high=module_params['m_high_aoi']/module_params['IscDNI_top']
    )
    
    uf_aoi_norm = uf_aoi / uf_aoi_ast
    
    uf_global = uf_am_at * uf_aoi_norm
    
    # (dc['p_mp'] * uf_global).plot()
    assert (dc['p_mp'] * uf_global).sum() == 6377.265283689235
