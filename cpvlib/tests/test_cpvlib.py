# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 18:18:09 2020

@author: Ruben
"""
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

import pvlib
from cpvlib import cpvsystem

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
    "b": 0.7,
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

mod_params_cpv.update(UF_parameters)

@pytest.fixture
def data():

    filename = Path(__file__).resolve().parent / 'data' /'InsolightMay2019.csv'

    data = pd.read_csv(filename, index_col='Date Time',
                       parse_dates=True, encoding='latin1')
    data.index = data.index.tz_localize('Europe/Madrid')
    
    data = data.rename(columns={
        'DNI (W/m2)': 'dni',
        'DII (W/m2)': 'dii',
        'GII (W/m2)': 'gii',
        'T_Amb (°C)': 'temp_air',
        'Wind Speed (m/s)': 'wind_speed',
        'T_Backplane (°C)': 'temp_cell_35',
        'ISC_measured_IIIV (A)':'isc35',
        'ISC_measured_Si (A)':'iscSi',
    })
    
    return data

test_data = [
    ('data/meteo2020_03_04.txt', 6377.265283689234),
    ('data/meteo2020_03_14.txt', 8494.147901845981),
]


@pytest.mark.parametrize("dia, energy", test_data)
def test_StaticCPVSystem_energy_daily(dia, energy):
    
    filename = Path(__file__).resolve().parent / dia

    meteo = pd.read_csv(
        filename, sep='\t', index_col='yyyy/mm/dd hh:mm', parse_dates=True)
    meteo.index = meteo.index.tz_localize('Europe/Madrid')

    location = pvlib.location.Location(
        latitude=40.4, longitude=-3.7, altitude=695, tz='Europe/Madrid')

    static_cpv_sys = cpvsystem.StaticCPVSystem(
        surface_tilt=30,
        surface_azimuth=180,
        module=None,
        module_parameters=mod_params_cpv,
        temperature_model_parameters=pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['pvsyst']['insulated'],
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
        # am_thld=mod_params_cpv['am_thld'],
        # am_uf_m_low=mod_params_cpv['am_uf_m_low']/mod_params_cpv['IscDNI_top'],
        # am_uf_m_high=mod_params_cpv['am_uf_m_high']/mod_params_cpv['IscDNI_top']
    )

    uf_ta = static_cpv_sys.get_tempair_util_factor(
        temp_air=meteo['Temp. Ai 1'],
        # ta_thld=mod_params_cpv['ta_thld'] ,
        # ta_uf_m_low=mod_params_cpv['ta_uf_m_low']/mod_params_cpv['IscDNI_top'],
        # ta_uf_m_high=mod_params_cpv['ta_uf_m_high']/mod_params_cpv['IscDNI_top']
    )

    uf_am_at = uf_am * mod_params_cpv['weight_am'] + \
        uf_ta * mod_params_cpv['weight_temp']

    # ax=meteo['dii'].plot();meteo['Bn'].plot(ax=ax)

    uf_aoi = static_cpv_sys.get_aoi_util_factor(
        aoi=static_cpv_sys.get_aoi(
            solar_zenith=location.get_solarposition(meteo.index).zenith,
            solar_azimuth=location.get_solarposition(meteo.index).azimuth,
        ),
        # aoi_thld=mod_params_cpv['aoi_thld'],
        # aoi_uf_m_low=mod_params_cpv['aoi_uf_m_low']/mod_params_cpv['IscDNI_top'],
        # aoi_uf_m_high=mod_params_cpv['aoi_uf_m_high']/mod_params_cpv['IscDNI_top']
    )

    uf_aoi_ast = static_cpv_sys.get_aoi_util_factor(
        aoi=0,
        # aoi_thld=mod_params_cpv['aoi_thld'],
        # aoi_uf_m_low=mod_params_cpv['aoi_uf_m_low']/mod_params_cpv['IscDNI_top'],
        # aoi_uf_m_high=mod_params_cpv['aoi_uf_m_high']/mod_params_cpv['IscDNI_top']
    )

    uf_aoi_norm = uf_aoi / uf_aoi_ast

    uf_global = uf_am_at * uf_aoi_norm

    assert (dc['p_mp'] * uf_global).sum() == energy

def test_StaticCPVSystem_energy_2019_05(data, energy=90509.11811618837):
    
    location = pvlib.location.Location(
        latitude=40.4, longitude=-3.7, altitude=695, tz='Europe/Madrid')
    
    solar_zenith = location.get_solarposition(data.index).zenith
    solar_azimuth = location.get_solarposition(data.index).azimuth
       
    static_cpv_sys = cpvsystem.StaticCPVSystem(
        surface_tilt=30,
        surface_azimuth=180,
        module=None,
        module_parameters=mod_params_cpv,
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
        data['dii_effective'], data['temp_cell_35'])
    
    dc_cpv = static_cpv_sys.singlediode(*diode_parameters_cpv)
    
    airmass_absolute = location.get_airmass(data.index).airmass_absolute
    
    # OJO uf_global NO incluye uf_aoi!!
    uf_global = static_cpv_sys.get_global_utilization_factor(airmass_absolute, data['temp_air'])
    
    assert (dc_cpv['p_mp'] * uf_global).sum() == energy
    
def test_StaticHybridSystem_composicion_2019_05(data):
   
    location = pvlib.location.Location(
        latitude=40.4, longitude=-3.7, altitude=695, tz='Europe/Madrid')
    
    solar_zenith = location.get_solarposition(data.index).zenith
    solar_azimuth = location.get_solarposition(data.index).azimuth
       
    # %% StaticCPVSystem
    static_cpv_sys = cpvsystem.StaticCPVSystem(
        surface_tilt=30,
        surface_azimuth=180,
        module=None,
        module_parameters=mod_params_cpv,
        temperature_model_parameters=pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['pvsyst']['insulated'],
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
        data['dii_effective'], data['temp_cell_35'])
    
    dc_cpv = static_cpv_sys.singlediode(*diode_parameters_cpv)
    
    airmass_absolute = location.get_airmass(data.index).airmass_absolute
    
    # OJO uf_global NO incluye uf_aoi!!
    uf_global = static_cpv_sys.get_global_utilization_factor(airmass_absolute, data['temp_air'])

    
    # %% StaticFlatPlateSystem
    # toma valores por defecto de mod_params_flatplate para método calcparams_pvsyst() en:
    # https://github.com/pvlib/pvlib-python/blob/e526b55365ab0f4c473b40b24ae8a82c7e42f892/pvlib/tests/conftest.py#L171-L191
    mod_params_flatplate = {
        "gamma_ref": 1.05,  # valor de test de calcparams_pvsyst()
        "mu_gamma": 0.001,  # valor de test de calcparams_pvsyst()
        "I_L_ref": 6.0,  # valor de test de calcparams_pvsyst()
        "I_o_ref": 5e-9,  # valor de test de calcparams_pvsyst()
        "R_sh_ref": 300,  # valor de test de calcparams_pvsyst()
        "R_sh_0": 1000,  # valor de test de calcparams_pvsyst()
        "R_sh_exp": 5.5,  # valor de test de calcparams_pvsyst()
        "R_s": 0.5,  # valor de test de calcparams_pvsyst()
        "alpha_sc": 0.001,  # valor de test de calcparams_pvsyst()
        "EgRef": 1.121,  # valor de test de calcparams_pvsyst()
        "irrad_ref": 1000,  # calcparams_pvsyst()
        "temp_ref": 25,  # calcparams_pvsyst()
        "cells_in_series": 12,  # calcparams_pvsyst()
        "cells_in_parallel": 48,
        "eta_m": 0.1,  # valor por defecto de pvsyst_celltemp()
        "alpha_absorption": 0.9,  # valor por defecto de pvsyst_celltemp()
        "aoi_limit": 55,
        # "Area": 1.2688,
        # "Impo": 8.3, # parámetro de sapm()
        # "Vmpo": 43.9, # parámetro de sapm()
    }
    
    static_flatplate_sys = cpvsystem.StaticFlatPlateSystem(
        surface_tilt=30,
        surface_azimuth=180,
        module=None,
        module_parameters=mod_params_flatplate,
        modules_per_string=1,
        strings_per_inverter=1,
        inverter=None,
        inverter_parameters=None,
        racking_model="insulated",
        losses_parameters=None,
        name=None,
    )
    
    # el aoi de difusa es el mismo que cpv
    data['poa_flatplate_static'] = static_flatplate_sys.get_irradiance(solar_zenith,
                                                                   solar_azimuth,
                                                                   aoi=data['aoi'],
                                                                   # aoi_limit=55, # ahora pasa por module_params
                                                                   # dii_effective no aplica, ya que si no el calculo de difusa es artificialmente alto!
                                                                   dii=data['dii'],
                                                                   gii=data['gii']
                                                                   )
    
    celltemp_flatplate = static_flatplate_sys.pvsyst_celltemp(
        data['poa_flatplate_static'], data['temp_air'], data['wind_speed']
    )
    
    diode_parameters_flatplate = static_flatplate_sys.calcparams_pvsyst(
        data['poa_flatplate_static'], celltemp_flatplate)
    
    dc_flatplate = static_flatplate_sys.singlediode(*diode_parameters_flatplate)

    # %% StaticHybridSystem
    static_hybrid_sys = cpvsystem.StaticHybridSystem(
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
    dii_effective_h, poa_flatplate_static_h = static_hybrid_sys.get_effective_irradiance(
        solar_zenith,
        solar_azimuth,
        # aoi_limit=55, # ahora pasa por module_params
        dni=data['dni'],
        # iam_param=0.7, # ahora pasa por module_params
        dii=None,  # dii_effective no aplica, ya que si no el calculo de difusa es artificialmente alto!
        gii=data['gii'],
    )

    assert np.allclose(data['dii_effective'], dii_effective_h, atol=1) is True
    assert np.allclose(data['poa_flatplate_static'],
                       poa_flatplate_static_h, atol=1) is True
    
    # pvsyst_celltemp
    _, celltemp_flatplate_h = static_hybrid_sys.pvsyst_celltemp(
        dii=dii_effective_h,
        poa_flatplate_static=poa_flatplate_static_h,
        temp_air=data['temp_air'],
        wind_speed=data['wind_speed']
    )
    
    assert np.allclose(celltemp_flatplate, celltemp_flatplate_h, atol=1) is True
    # celltemp_flatplate.plot()
    # celltemp_flatplate_h.plot()
    
    # calcparams_pvsyst
    diode_parameters_cpv_h, diode_parameters_flatplate_h = static_hybrid_sys.calcparams_pvsyst(
        dii=dii_effective_h,
        poa_flatplate_static=poa_flatplate_static_h,
        temp_cell_cpv=data['temp_cell_35'],
        temp_cell_flatplate=celltemp_flatplate_h,
    )
    
    for diode_param, diode_param_h in zip(diode_parameters_cpv, diode_parameters_cpv_h):
        assert np.allclose(diode_param, diode_param_h, atol=10) is True
    
    # (diode_param - diode_param_h).plot()
    
    # singlediode
    airmass_absolute = location.get_airmass(data.index).airmass_absolute
    dc_cpv_h, dc_flatplate_h = static_hybrid_sys.singlediode(
        diode_parameters_cpv_h, diode_parameters_flatplate_h)
    
    for dc_param in dc_cpv:
        assert np.allclose(dc_cpv[dc_param], dc_cpv_h[dc_param], atol=1) is True
    
    for dc_param in dc_cpv:
        assert np.allclose(dc_flatplate[dc_param].fillna(
            0), dc_flatplate_h[dc_param].fillna(0), atol=100) is True
    
    # dc_flatplate[dc_param].plot()
    # dc_flatplate_h[dc_param].plot()
    # (dc_flatplate[dc_param] - dc_flatplate_h[dc_param]).plot()
    
    # uf_global
    airmass_absolute = location.get_airmass(data.index).airmass_absolute
    
    uf_global_h = static_hybrid_sys.get_global_utilization_factor_cpv(airmass_absolute, data['temp_air'])
    
    assert np.allclose(uf_global, uf_global_h, atol=0.001) is True


##############################

def test_StaticCPVSystem_get_aoi():
    static_cpvsystem = cpvsystem.StaticCPVSystem(surface_tilt=32, surface_azimuth=135)
    aoi = static_cpvsystem.get_aoi(30, 225)
    assert np.round(aoi, 4) == 42.7408

def test_StaticCPVSystem_get_irradiance():
    static_cpvsystem = cpvsystem.StaticCPVSystem(surface_tilt=32, surface_azimuth=135)
    times = pd.date_range(start='20160101 1200-0700',
                          end='20160101 1800-0700', freq='6H')
    location = pvlib.location.Location(latitude=32, longitude=-111)
    solar_position = location.get_solarposition(times)
    dni = pd.Series([900, 0], index=times)

    irradiance = static_cpvsystem.get_irradiance(solar_position['apparent_zenith'],
                                       solar_position['azimuth'],
                                       dni)

    expected = pd.Series(data=np.array([745.861417,  0.0]), index=times)

    pd.testing.assert_series_equal(irradiance, expected, rtol=0.0001)
