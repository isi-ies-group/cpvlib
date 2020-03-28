# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 18:18:09 2020

@author: Ruben
"""
import pandas as pd
import pytest

import pvlib
import cpvlib

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

UF_parameters = {
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

module_params_cpv.update(UF_parameters)

test_data = [
    ('meteo2020_03_04.txt', 6377.265283689235),
    ('meteo2020_03_14.txt', 8494.147901845981),
]


@pytest.mark.parametrize("dia, energy", test_data)
def test_StaticCPVSystem_energy_daily(dia, energy):

    meteo = pd.read_csv(
        dia, sep='\t', index_col='yyyy/mm/dd hh:mm', parse_dates=True)
    meteo.index = meteo.index.tz_localize('Europe/Madrid')

    location = pvlib.location.Location(
        latitude=40.4, longitude=-3.7, altitude=695, tz='Europe/Madrid')

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
        # am_thld=module_params_cpv['am_thld'],
        # am_uf_m_low=module_params_cpv['am_uf_m_low']/module_params_cpv['IscDNI_top'],
        # am_uf_m_high=module_params_cpv['am_uf_m_high']/module_params_cpv['IscDNI_top']
    )

    uf_ta = static_cpv_sys.get_tempair_util_factor(
        temp_air=meteo['Temp. Ai 1'],
        # ta_thld=module_params_cpv['ta_thld'] ,
        # ta_uf_m_low=module_params_cpv['ta_uf_m_low']/module_params_cpv['IscDNI_top'],
        # ta_uf_m_high=module_params_cpv['ta_uf_m_high']/module_params_cpv['IscDNI_top']
    )

    uf_am_at = uf_am * module_params_cpv['weight_am'] + \
        uf_ta * module_params_cpv['weight_temp']

    # ax=meteo['dii'].plot();meteo['Bn'].plot(ax=ax)

    uf_aoi = static_cpv_sys.get_aoi_util_factor(
        aoi=static_cpv_sys.get_aoi(
            solar_zenith=location.get_solarposition(meteo.index).zenith,
            solar_azimuth=location.get_solarposition(meteo.index).azimuth,
        ),
        # aoi_thld=module_params_cpv['aoi_thld'],
        # aoi_uf_m_low=module_params_cpv['aoi_uf_m_low']/module_params_cpv['IscDNI_top'],
        # aoi_uf_m_high=module_params_cpv['aoi_uf_m_high']/module_params_cpv['IscDNI_top']
    )

    uf_aoi_ast = static_cpv_sys.get_aoi_util_factor(
        aoi=0,
        # aoi_thld=module_params_cpv['aoi_thld'],
        # aoi_uf_m_low=module_params_cpv['aoi_uf_m_low']/module_params_cpv['IscDNI_top'],
        # aoi_uf_m_high=module_params_cpv['aoi_uf_m_high']/module_params_cpv['IscDNI_top']
    )

    uf_aoi_norm = uf_aoi / uf_aoi_ast

    uf_global = uf_am_at * uf_aoi_norm

    assert (dc['p_mp'] * uf_global).sum() == energy

def test_StaticCPVSystem_energy_2019_05(energy=90509.11811618837):
    
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
     
    location = pvlib.location.Location(
        latitude=40.4, longitude=-3.7, altitude=695, tz='Europe/Madrid')
    
    solar_zenith = location.get_solarposition(data.index).zenith
    solar_azimuth = location.get_solarposition(data.index).azimuth
       
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
    
    assert (dc_cpv['p_mp'] * uf_global).sum() == energy