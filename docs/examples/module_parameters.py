# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 01:39:37 2020

@author: Ruben, Cesar
"""

# XX m2, XXX III-V cells (12 serie x XX parallel) micro-cells + XX Y"(ZZ cm) Si-cells in series
# https://doi.org/10.5281/zenodo.3349781
# 35 range IV: 0.7 A, 35 V @DNI 900 W/m2
# Si range IV: 1.7 A, 2.2 V @GNI 950 W/m2 & DNI/GNI=0.7

# https://pvlib-python.readthedocs.io/en/stable/generated/pvlib.pvsystem.calcparams_pvsyst.html

# mod 191
mod_params_cpv = {
    "gamma_ref": 5.25, # Voltage adjustment. Previous 5.524
    "mu_gamma": 0.0004,
    "I_L_ref": 0.97*5,
    "I_o_ref": 1.7e-10, 
    "R_sh_ref": 5226,
    "R_sh_0": 21000,
    "R_sh_exp": 5.50,
    "R_s": 0.01,
    "alpha_sc": 0.00,
    "EgRef": 3.94,
    "irrad_ref": 1000,
    "temp_ref": 25,
    "cells_in_series": 12,
    "eta_m": 0.32,
    "alpha_absorption": 0.9,
    #"b": 0.7,
    "iam_model": 'interp',
    "theta_ref": [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 54, 55, 56,90],
    "iam_ref": [1.000, 1.007, 0.998, 0.991, 0.971, 0.966, 0.938, 0.894, 0.830, 0.790, 0.740, 0.649, 0.1, 0.002,0.001],
}

UF_parameters_cpv = {
    "IscDNI_top": 1,
    "am_thld": 1.25,
    "am_uf_m_low": 0.4, #0.175
    "am_uf_m_high": -0.5,  
    "ta_thld": 15, #original 15.2
    "ta_uf_m_low": 0.0, 
    "ta_uf_m_high": -0.00, 
    "weight_am": 1,
    "weight_temp": 0,
}

mod_params_cpv.update(UF_parameters_cpv)

# mod 120
mod_params_flatplate = {
    "gamma_ref": 1.1, #ideality factor
    "mu_gamma": -0.0003,
    "I_L_ref": 2.05,
    "I_o_ref": 1.5e-10,
    "R_sh_ref": 200,
    "R_sh_0": 600, # 4 times Rsh_ref typically acc. PVSYST
    "R_sh_exp": 5.5,
    "R_s": 0.6, #standard value
    "alpha_sc": 0,
    "EgRef": 1.121,
    "irrad_ref": 1000,
    "temp_ref": 25,
    "cells_in_series": 64, # 8*8,
    "eta_m": 0.2,  # module efficiency for pvlib.temperature.pvsyst_cell
    "alpha_absorption": 0.6,  # more light is absorbed in the front cover than in conventional flat plate
    "aoi_limit": 40, #should be 55°, but tracking mechanism is not working welll
    "iam_model": 'interp',
    "theta_ref": [0, 5, 15, 25, 35, 45,  55,   65,   70,   80,   85, 90],
    "iam_ref":   [1, 1, 1,  1,  1,  1, 0.95,  0.7,  0.5,  0.5,  0.5, 0],
    # "iam_ref": [1,  1,  0.9918,  0.9815,  0.9721,  0.9485,  0.9071,  0.6072,  0.00365,  0,  0] #THEIA cSI notebook
    
    "theta_ref_spillage": [0, 10, 20, 30, 40,  55, 90],
    "iam_ref_spillage": [1, 1, 1.02, 1.16,  1.37, 1.37, 1.37]
}
