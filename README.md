# cpvlib ![Python package](https://github.com/isi-ies-group/cpvlib/workflows/Python%20package/badge.svg)
The `cpvlib` library is a layer over [`pvlib-python`](https://github.com/pvlib/pvlib-python) that models CPV systems.

It is built in file `cpvlib.py`, that contains the following classes:

* CPVSystem
* StaticCPVSystem
* StaticFlatPlateSystem
* StaticHybridSystem

## Library installation & usage
`pip install --upgrade git+https://github.com/isi-ies-group/cpvlib.git`

`from cpvlib import cpvlib`
`cpvlib.StaticHybridSystem(...)`

## Live Jupyter notebook demo without installation (on external server)
* StaticHybridSystem_tmy.ipynb [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/isi-ies-group/cpvlib/master?filepath=cpvlib/StaticHybridSystem_tmy.ipynb)

## TO DO
* [x] Fitting of the Insolight flat plate subsystem
* [ ] Fitting the IAM of the Insolight flat plate subsystem
* [x] When the code stabilizes, put all the parameters in the class constructors
* [ ] Put 'spillage' parameter in class constructor
* [ ] Homogenize piecewise functions for Utility Factors and IAM
* [ ] Add more tests: flat plate part

Testing dataset [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3346823.svg)](https://doi.org/10.5281/zenodo.3346823)
