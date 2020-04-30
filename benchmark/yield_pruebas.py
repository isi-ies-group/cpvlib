# -*- coding: utf-8 -*-
"""
Created on Thu Apr 30 18:38:50 2020

@author: Ruben
"""


# %% SAPM
# sandia_modules = pvlib.pvsystem.retrieve_sam('SandiaMod')
# module = sandia_modules['Canadian_Solar_CS5P_220M___2009_']

# pv2 = pvlib.pvsystem.PVSystem(
#     module_parameters=module,
#     surface_tilt=40,
#     surface_azimuth=0,
#     # albedo=0.2,
#     # temperature_model_parameters=temperature_model_parameters,
#     modules_per_string=1,
#     inverter_per_string=1,
# )

# pv_irr2 = pv2.get_irradiance(
#     solar_zenith=solpos['zenith'],
#     solar_azimuth=solpos['azimuth'],
#     ghi=data['ghi'],
#     dhi=data['dhi'],
#     dni=data['dni']
# )

# pv_cell_temp2 = pv2.pvsyst_celltemp(
#     poa_global=pv_irr2['poa_global'],
#     temp_air=data['temp_air'],
#     wind_speed=data['wind_speed']
#     )

# pv_power2 = pv2.sapm(
#     effective_irradiance = pv_irr2['poa_global'],
#     temp_cell = pv_cell_temp2,
#     )

# pv2.sapm(
#     effective_irradiance = 1000,
#     temp_cell = 25,
#     )

# Pdc_nom = 220 # W

# Yr = pv_irr2['poa_global'].sum() / 1000
# Ya = pv_power2['p_mp'].sum() / Pdc_nom

# Lc = Yr - Ya

# PR = Ya / Yr

# print(PR, Ya, Yr)

# data.ghi.plot(grid=True);pv_irr2.poa_global.plot()

# %% TMY3
# data_tmy3 = pvlib.iotools.read_tmy3('722689TYA.csv')

# data = data_tmy3[0].rename(columns={
#     'DNI': 'dni',
#     'GHI': 'ghi',
#     'DHI': 'dhi',
#     'DryBulb': 'temp_air',
#     'Wspd': 'wind_speed',
# })
# meta = data_tmy3[1]
# location2 = pvlib.location.Location(
#     latitude=meta['latitude'], longitude=meta['longitude'], altitude=meta['altitude'], tz='US/Mountain')
