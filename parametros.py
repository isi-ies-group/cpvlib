# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 01:39:37 2020

@author: Ruben
"""

# https://doi.org/10.5281/zenodo.3346823
# 0.1 m2, 572 (12 serie x 48 parallel) micro-cells + 4x 6"(15.24 cm) Si-cells in series
# https://doi.org/10.5281/zenodo.3349781
# 35 rango IV: 0.7 A, 35 V @DNI 900 W/m2
# Si rango IV: 1.7 A, 2.2 V @GNI 950 W/m2 y DNI/GNI=0.7

# https://pvlib-python.readthedocs.io/en/stable/generated/pvlib.pvsystem.calcparams_pvsyst.html
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
    "cells_in_series": 4,  # visto Vmp~=Pmp/Isc
    # "cells_in_parallel": 48, # 
    "eta_m": 0.1,  # valor por defecto de pvsyst_celltemp()
    "alpha_absorption": 0.9,  # valor por defecto de pvsyst_celltemp()
    # "Area": 1.2688,
    # "Impo": 8.3, # parámetro de sapm()
    # "Vmpo": 43.9, # parámetro de sapm()
}

params_tracker = {
    'axis_tilt':0,
    'axis_azimuth':0,
    'max_angle':90,
    'backtrack':True,
    'gcr':2.0/7.0
}