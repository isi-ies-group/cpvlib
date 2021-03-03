# cpvlib ![Python package](https://github.com/isi-ies-group/cpvlib/workflows/Python%20package/badge.svg)
The `cpvlib` library is a layer over [`pvlib-python`](https://github.com/pvlib/pvlib-python) that models CPV systems.

It is built in file `cpvlib.py`, that contains the `cpvsystem` module with following classes:

* CPVSystem
* StaticCPVSystem
* StaticFlatPlateSystem
* StaticHybridSystem

## Library installation & usage
`pip install --force-reinstall --no-deps git+https://github.com/isi-ies-group/cpvlib.git`

`from cpvlib import cpvsystem`
`cpvsystem.StaticHybridSystem(...)`

## Live Jupyter notebook demo without installation (on Binder)
* StaticHybridSystem_tmy.ipynb [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/isi-ies-group/cpvlib/master?filepath=docs/examples/StaticHybridSystem_tmy.ipynb)

Testing dataset [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3346823.svg)](https://doi.org/10.5281/zenodo.3346823)
