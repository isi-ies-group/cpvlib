# -*- coding: utf-8 -*-
"""
Modified on Wed Oct 20 14:43:00 2021

@author: Ruben, César
"""

# Active surface: 0.54 m2
# CPV sub-module: III-V 3J solar cells, 216 parallel, 14 series
# Flat plate sub-module: Si IBC solar cells, 64 in series
# https://doi.org/10.5281/zenodo.3349781
# 35 range IV: 0.7 A, 35 V @DNI 900 W/m2
# Si range IV: 1.7 A, 2.2 V @GNI 950 W/m2 & DNI/GNI=0.7

# https://pvlib-python.readthedocs.io/en/stable/generated/pvlib.pvsystem.calcparams_pvsyst.html

mod_params_cpv = {
    "gamma_ref": 5.25, # Voltage adjustment. Previous 5.524
    "mu_gamma": 0.0004,
    "I_L_ref": 1*5,
    "I_o_ref": 9e-10, 
    "R_sh_ref": 5226,
    "R_sh_0": 21000,
    "R_sh_exp": 5.50,
    "R_s": 0.01,
    "alpha_sc": 0.00,
    "EgRef": 3.94,
    "irrad_ref": 1000,
    "temp_ref": 25,
    "cells_in_series": 14,
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

# 191 module does not include Si submodule
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
    "aoi_limit": 40, #should be 55°, buttracking mechanism is not working welll
    "iam_model": 'interp',
    "theta_ref": [0, 5, 15, 25, 35, 45,  55,   65,   70,   80,   85, 90],
    "iam_ref":   [1, 1, 1,  1,  1,  1, 0.95,  0.7,  0.5,  0.5,  0.5, 0],
    # "iam_ref": [1,  1,  0.9918,  0.9815,  0.9721,  0.9485,  0.9071,  0.6072,  0.00365,  0,  0] #THEIA cSI notebook
    
    "theta_ref_spillage": [0, 10, 20, 30, 40, 50, 55, 90],
    "iam_ref_spillage": [1, 1, 1.02, 1.16,  1.37, 1.37, 1.37, 1.37] #Use if global spillage is 0.15
    # "iam_ref_spillage": [1, 1, 1, 1,  1, 1, 1] #Use for no angular variation of spillage
    
}



#OLD DEPRECATED PARAMETERS
#mod_params_cpv = {
#    "gamma_ref": 5.524,
#    "mu_gamma": 0.003,
#    "I_L_ref": 0.96*0.9,
#    "I_o_ref": 1.7e-10,
#    "R_sh_ref": 5226,
#    "R_sh_0": 21000,
#    "R_sh_exp": 5.50,
#    "R_s": 0.01,
#    "alpha_sc": 0.00,
#    "EgRef": 3.91,
#    "irrad_ref": 1000,
#    "temp_ref": 25,
#    "cells_in_series": 12,
#    "eta_m": 0.32,
#    "alpha_absorption": 0.9,
#    "b": 0.7,
#    "iam_model": 'ashrae',
#    "theta_ref": [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60],
#    "iam_ref": [1.000, 1.007, 0.998, 0.991, 0.971, 0.966, 0.938, 0.894, 0.830, 0.790, 0.740, 0.649, 0.387],
#}
#
#UF_parameters_cpv = {
#    "IscDNI_top": 0.96 / 1000,
#    "am_thld": 4.574231933073185,
#    "am_uf_m_low": 3.906372068620377e-06,
#    "am_uf_m_high": -3.0335768119184845e-05,
#    "ta_thld": 50,
#    "ta_uf_m_low": 4.6781224141650075e-06,
#    "ta_uf_m_high": 0,
#    "weight_am": 0.2,
#    "weight_temp": 0.8,
#}
#
#mod_params_cpv.update(UF_parameters_cpv)
#
## example (NO Insolight) PV module from:
## https://pvpmc.sandia.gov/PVLIB_Matlab_Help/html/pvl_calcparams_PVsyst_help.html
#mod_params_flatplate = {
#    "gamma_ref": 1.1,
#    "mu_gamma": -0.0003,
#    "I_L_ref": 8,
#    "I_o_ref": 2.2e-9,
#    "R_sh_ref": 200,
#    "R_sh_0": 8700,
#    "R_sh_exp": 5.5,
#    "R_s": 0.33,
#    "alpha_sc": -0.002,
#    "EgRef": 1.121,
#    "irrad_ref": 1000,
#    "temp_ref": 25,
#    "cells_in_series": 4, # 60,
#    "eta_m": 0.95,  # pvsyst_celltemp() default value
#    "alpha_absorption": 0.97,  # pvsyst_celltemp() default value
#    "aoi_limit": 55,
#}
