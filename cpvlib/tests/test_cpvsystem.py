# -*- coding: utf-8 -*-
"""
Created on Sun Feb  7 23:16:16 2021

@author: Ruben
"""
import pandas as pd
import numpy as np

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
    "iam_model": 'ashrae',
    "theta_ref": [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60],
    "iam_ref": [1.000, 1.007, 0.998, 0.991, 0.971, 0.966, 0.938, 0.894, 0.830, 0.790, 0.740, 0.649, 0.387],
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

# takes default values from mod_params_flatplate for calcparams_pvsyst() method in:
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

##############################


def test_CPVSystem_get_irradiance():
    cpv_system = cpvsystem.CPVSystem()
    times = pd.date_range(start='20160101 1200-0700',
                          end='20160101 1800-0700', freq='6H')
    location = pvlib.location.Location(latitude=32, longitude=-111)
    solar_position = location.get_solarposition(times)
    irrads = pd.DataFrame({'dni': [900, 0], 'ghi': [600, 0], 'dhi': [100, 0]},
                          index=times)

    irradiance = cpv_system.get_irradiance(solar_position['apparent_zenith'],
                                           solar_position['azimuth'],
                                           irrads['dni'],
                                           irrads['ghi'],
                                           irrads['dhi'])

    expected = pd.DataFrame(data=np.array(
        [[992.902225, 841.741664, 151.160560, 137.869177, 13.291383],
         [0.,   -0.,    0.,    0.,    0.]]),
        columns=['poa_global', 'poa_direct',
                 'poa_diffuse', 'poa_sky_diffuse',
                 'poa_ground_diffuse'],
        index=times)

    pd.testing.assert_frame_equal(irradiance, expected, rtol=0.0001)


def test_CPVSystem_pvsyst_celltemp(mocker):
    parameter_set = 'freestanding'
    temp_model_params = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['pvsyst'][
        parameter_set]

    cpv_system = cpvsystem.CPVSystem(module_parameters=mod_params_cpv,
                                     temperature_model_parameters=temp_model_params)
    irrad = 800
    temp = 45
    wind = 0.5

    mocker.spy(pvlib.temperature, 'pvsyst_cell')
    out = cpv_system.pvsyst_celltemp(irrad, temp, wind)

    pvlib.temperature.pvsyst_cell.assert_called_once_with(
        irrad, temp, wind, temp_model_params['u_c'], temp_model_params['u_v'],
        mod_params_cpv['eta_m'], mod_params_cpv['alpha_absorption'])

    assert np.round(out, 4) == 61.8828


def test_CPVSystem_get_am_util_factor():
    cpv_system = cpvsystem.CPVSystem(module_parameters=mod_params_cpv)

    times = pd.date_range(start='20160101 1200',
                          end='20160101 1500', freq='3H')

    airmass_absolute = pd.Series(
        data=np.array([2.056997, 3.241064]), index=times)

    am_uf = cpv_system.get_am_util_factor(airmass_absolute)

    expected = pd.Series(data=np.array([0.989757, 0.994575]), index=times)

    pd.testing.assert_series_equal(am_uf, expected, rtol=0.0001)


def test_CPVSystem_get_tempair_util_factor():
    cpv_system = cpvsystem.CPVSystem(module_parameters=mod_params_cpv)

    times = pd.date_range(start='20160101 1200',
                          end='20160101 1500', freq='3H')

    temp_air = pd.Series(data=np.array([5, 35]), index=times)

    ta_uf = cpv_system.get_am_util_factor(temp_air)

    expected = pd.Series(data=np.array([0.986546, 0.038553]), index=times)

    pd.testing.assert_series_equal(ta_uf, expected, rtol=0.0001)


def test_CPVSystem_get_global_utilization_factor():
    cpv_system = cpvsystem.CPVSystem(module_parameters=mod_params_cpv)

    times = pd.date_range(start='20160101 1200',
                          end='20160101 1500', freq='3H')

    airmass_absolute = pd.Series(
        data=np.array([2.056997, 3.241064]), index=times)
    temp_air = pd.Series(data=np.array([5, 35]), index=times)

    uf_global = cpv_system.get_global_utilization_factor(
        airmass_absolute, temp_air)

    expected = pd.Series(data=np.array([0.822522, 0.940439]), index=times)

    pd.testing.assert_series_equal(uf_global, expected, rtol=0.0001)

##############################


def test_StaticCPVSystem_get_aoi():
    static_cpvsystem = cpvsystem.StaticCPVSystem(
        surface_tilt=32, surface_azimuth=135)
    aoi = static_cpvsystem.get_aoi(30, 225)

    assert np.round(aoi, 4) == 42.7408


def test_StaticCPVSystem_get_iam_ashrae():
    static_cpvsystem = cpvsystem.StaticCPVSystem(
        module_parameters=mod_params_cpv)
    aoi = static_cpvsystem.get_aoi(30, 225)
    iam = static_cpvsystem.get_iam(aoi, iam_model='ashrae')

    assert np.round(iam, 4) == 0.8917


def test_StaticCPVSystem_get_iam_interp():

    static_cpvsystem = cpvsystem.StaticCPVSystem(
        module_parameters=mod_params_cpv)
    iam = static_cpvsystem.get_iam(42, iam_model='interp')

    assert np.round(iam, 4) == 0.814


def test_StaticCPVSystem_get_irradiance():
    static_cpvsystem = cpvsystem.StaticCPVSystem(
        surface_tilt=32, surface_azimuth=135)
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


def test_StaticCPVSystem_get_effective_irradiance():
    static_cpvsystem = cpvsystem.StaticCPVSystem(
        surface_tilt=32, surface_azimuth=135, module_parameters=mod_params_cpv)
    times = pd.date_range(start='20160101 1200-0700',
                          end='20160101 1800-0700', freq='6H')
    location = pvlib.location.Location(latitude=32, longitude=-111)
    solar_position = location.get_solarposition(times)
    dni = pd.Series([900, 0], index=times)

    eff_irr = static_cpvsystem.get_effective_irradiance(solar_position['apparent_zenith'],
                                                        solar_position['azimuth'],
                                                        dni)

    expected = pd.Series(data=np.array([637.964408,  0.0]), index=times)

    pd.testing.assert_series_equal(eff_irr, expected, rtol=0.0001)

##############################


def test_StaticFlatPlateSystem_get_aoi():
    static_flatsystem = cpvsystem.StaticFlatPlateSystem(
        surface_tilt=32, surface_azimuth=135)
    aoi = static_flatsystem.get_aoi(30, 225)
    assert np.round(aoi, 4) == 42.7408

# FUNCTION TO BE VALIDATED
# def test_StaticFlatPlateSystem_get_iam():
#     static_flatsystem = cpvsystem.StaticFlatPlateSystem(
# module_parameters=mod_params_cpv)
#     aoi = static_flatsystem.get_aoi(30, 225)
#     iam = static_flatsystem.get_iam(aoi, iam_model=mod_params_cpv['iam_model'])
#     assert np.round(iam, 4) == 0.8917


def test_StaticFlatPlateSystem_get_irradiance():
    static_flatsystem = cpvsystem.StaticFlatPlateSystem(
        surface_tilt=32, surface_azimuth=135, module_parameters=mod_params_flatplate)
    times = pd.date_range(start='20160101 1200-0700',
                          end='20160101 1800-0700', freq='6H')
    location = pvlib.location.Location(latitude=32, longitude=-111)
    solar_position = location.get_solarposition(times)
    irrads = pd.DataFrame({'dni': [900, 0], 'ghi': [600, 0], 'dhi': [100, 0]},
                          index=times)
    irradiance = static_flatsystem.get_irradiance(solar_position['apparent_zenith'],
                                                  solar_position['azimuth'],
                                                  irrads['dni'],
                                                  irrads['ghi'],
                                                  irrads['dhi'])

    expected = pd.Series(data=np.array([137.794154,  0.0]), index=times)

    pd.testing.assert_series_equal(irradiance, expected, rtol=0.0001)


def test_StaticFlatPlateSystem_get_effective_irradiance():
    static_flatsystem = cpvsystem.StaticFlatPlateSystem(
        surface_tilt=32, surface_azimuth=135, module_parameters=mod_params_flatplate)
    times = pd.date_range(start='20160101 1200-0700',
                          end='20160101 1800-0700', freq='6H')
    location = pvlib.location.Location(latitude=32, longitude=-111)
    solar_position = location.get_solarposition(times)
    irrads = pd.DataFrame({'dni': [900, 0], 'ghi': [600, 0], 'dhi': [100, 0]},
                          index=times)
    eff_irr = static_flatsystem.get_effective_irradiance(solar_position['apparent_zenith'],
                                                         solar_position['azimuth'],
                                                         irrads['dni'],
                                                         irrads['ghi'],
                                                         irrads['dhi'])

    expected = pd.Series(data=np.array([137.794154,  0.0]), index=times)

    pd.testing.assert_series_equal(eff_irr, expected, rtol=0.0001)


def test_StaticFlatPlateSystem_pvsyst_celltemp(mocker):
    parameter_set = 'freestanding'
    temp_model_params = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['pvsyst'][
        parameter_set]

    static_flatsystem = cpvsystem.StaticFlatPlateSystem(module_parameters=mod_params_flatplate,
                                                        temperature_model_parameters=temp_model_params)
    irrad = 150
    temp = 45
    wind = 0.5

    mocker.spy(pvlib.temperature, 'pvsyst_cell')
    out = static_flatsystem.pvsyst_celltemp(irrad, temp, wind)

    pvlib.temperature.pvsyst_cell.assert_called_once_with(
        irrad, temp, wind, temp_model_params['u_c'], temp_model_params['u_v'],
        mod_params_flatplate['eta_m'], mod_params_flatplate['alpha_absorption'])

    assert np.round(out, 4) == 49.1897

##############################


def test_StaticHybridSystem_get_effective_irradiance():
    static_hybsystem = cpvsystem.StaticHybridSystem(
        surface_tilt=32, surface_azimuth=135, module_parameters_cpv=mod_params_cpv,
        module_parameters_flatplate=mod_params_flatplate)
    times = pd.date_range(start='20160101 1200-0700',
                          end='20160101 1800-0700', freq='6H')
    location = pvlib.location.Location(latitude=32, longitude=-111)
    solar_position = location.get_solarposition(times)
    irrads = pd.DataFrame({'dni': [900, 0], 'ghi': [600, 0], 'dhi': [100, 0]},
                          index=times)
    eff_irr_cpv, wff_irr_flat = static_hybsystem.get_effective_irradiance(solar_position['apparent_zenith'],
                                                                          solar_position['azimuth'],
                                                                          irrads['dni'],
                                                                          irrads['ghi'],
                                                                          irrads['dhi'])

    expected_cpv = pd.Series(data=np.array([637.964408,  0.0]), index=times)
    expected_flat = pd.Series(data=np.array([137.794154,  0.0]), index=times)

    pd.testing.assert_series_equal(eff_irr_cpv, expected_cpv, rtol=0.0001)
    pd.testing.assert_series_equal(wff_irr_flat, expected_flat, rtol=0.0001)


def test_HybridSystem_pvsyst_celltemp():

    parameter_set = 'freestanding'
    temp_model_params_cpv = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['pvsyst'][
        parameter_set]
    temp_model_params_flat = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['pvsyst'][
        parameter_set]

    static_hybsystem = cpvsystem.StaticHybridSystem(
        module_parameters_cpv=mod_params_cpv,
        module_parameters_flatplate=mod_params_flatplate,
        temperature_model_parameters_cpv=temp_model_params_cpv,
        temperature_model_parameters_flatplate=temp_model_params_flat)

    irrad_cpv = 800
    irrad_flat = 150
    temp = 45
    wind = 0.5

    out_cpv, out_flat = static_hybsystem.pvsyst_celltemp(
        irrad_cpv, irrad_flat, temp, wind)

    assert np.round(out_cpv, 4) == 61.8828
    assert np.round(out_flat, 4) == 49.1897


def test_HybridSystem_calcparams_pvsyst():

    static_hybsystem = cpvsystem.StaticHybridSystem(
        module_parameters_cpv=mod_params_cpv,
        module_parameters_flatplate=mod_params_flatplate)

    irrad_cpv = 800
    irrad_flat = 150
    temp_cell_cpv = 65
    temp_cell_flat = 50

    diode_parameters_cpv, diode_parameters_flat = static_hybsystem.calcparams_pvsyst(
        irrad_cpv, irrad_flat, temp_cell_cpv, temp_cell_flat)

    assert diode_parameters_cpv == (
        0.768, 6.021260125175771e-09, 0.01, 5355.728196448678, 1.973560253332227)
    assert diode_parameters_flat == (
        0.90375, 1.4707860128864193e-07, 0.5, 605.1508364413314, 0.35922505316643616)


def test_HybridSystem_singlediode():

    from collections import OrderedDict

    static_hybsystem = cpvsystem.StaticHybridSystem(
        module_parameters_cpv=mod_params_cpv,
        module_parameters_flatplate=mod_params_flatplate)

    diode_parameters_cpv = (0.768, 6.021260125175771e-09,
                            0.01, 5355.728196448678, 1.973560253332227)
    diode_parameters_flat = (
        0.90375, 1.4707860128864193e-07, 0.5, 605.1508364413314, 0.35922505316643616)

    dc_cpv, dc_flat = static_hybsystem.singlediode(
        diode_parameters_cpv, diode_parameters_flat)

    assert dc_cpv == OrderedDict([('i_sc', 0.7679985660005298),
                                  ('v_oc', 36.81679129270333),
                                  ('i_mp', 0.7169288240780115),
                                  ('v_mp', 31.238496992958595),
                                  ('p_mp', 22.395778915126304),
                                  ('i_x', 0.7644934769583084),
                                  ('i_xx', 0.5758846117534837)])

    assert dc_flat == OrderedDict([('i_sc', 0.903003532284735),
                                   ('v_oc', 5.6113766436897095),
                                   ('i_mp', 0.8210320675081583),
                                   ('v_mp', 4.310035383000505),
                                   ('p_mp', 3.5386772615382216),
                                   ('i_x', 0.8971082731548178),
                                   ('i_xx', 0.5712911044697004)])


def test_HybridSystem_get_global_utilization_factor_cpv():

    static_hybsystem = cpvsystem.StaticHybridSystem(
        module_parameters_cpv=mod_params_cpv,
        module_parameters_flatplate=mod_params_flatplate)

    times = pd.date_range(start='20160101 1200',
                          end='20160101 1500', freq='3H')

    airmass_absolute = pd.Series(
        data=np.array([2.056997, 3.241064]), index=times)
    temp_air = pd.Series(data=np.array([5, 35]), index=times)

    uf_global = static_hybsystem.get_global_utilization_factor_cpv(
        airmass_absolute, temp_air)

    expected = pd.Series(data=np.array([0.822522, 0.940439]), index=times)

    pd.testing.assert_series_equal(uf_global, expected, rtol=0.0001)
