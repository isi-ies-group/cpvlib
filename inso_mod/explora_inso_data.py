# -*- coding: utf-8 -*-
"""
Created on Wed Apr 15 00:18:25 2020

@author: Ruben
"""
import matplotlib.pyplot as plt
import pandas as pd

from pathlib import Path

path_inso = Path.home().joinpath('Desktop/modulos_insolight')

data_3mod = pd.concat([pd.read_csv(f, parse_dates=True, sep='\t',
                                   index_col='time') for f in path_inso.glob(f'*.txt')])

# ['panel_v', 'panel_c', 'panel_v2', 'panel_c2', 'panel_t', 'panel_rh',
# 'cell_min', 'cell_avg', 'cell_max', 'gii']

# %% Plot histograma variables 3 modulos
for num in [24, 29, 31]:
    data = data_3mod[data_3mod['ctrl_id'] == num]

    # data.drop(columns=['log_id', 'ctrl_id', 'ctrl_mode']).hist(bins=50)
    # plt.suptitle(f'mod:{num}')
    # plt.tight_layout()
    # plt.savefig(f'hist_{num}.png')

    # data.query('gii>500')[['panel_v', 'panel_c',
    #                        'panel_v2', 'panel_c2']].hist(bins=50)
    # plt.suptitle(f'mod:{num} gii>500')
    # plt.tight_layout()
    # plt.savefig(f'hist_iv_{num}.png')
    
    print(num, 
          data.query('gii>500')[['panel_v', 'panel_c', 'panel_v2', 'panel_c2']].describe())

# https://zenodo.org/record/3349781#.XpcyIMgzaUk
# 35 rango IV: 0.7 A, 35 V @DNI 900 W/m2
# Si rango IV: 1.7 A, 2.2 V @GNI 950 W/m2 y DNI/GNI=0.7

# %% mod 29: T,RH?
data_3mod.query('ctrl_id==29')[['panel_rh', 'panel_t']].hist(bins=50)

#%% mod todos: corriente c2
data_3mod.query('ctrl_id==24')['panel_c2'].plot()
data_3mod.query('ctrl_id==29')['panel_c2'].plot()
data_3mod.query('ctrl_id==31')['panel_c2'].plot()
