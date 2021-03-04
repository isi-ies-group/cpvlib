# cpvlib ![Python package](https://github.com/isi-ies-group/cpvlib/workflows/Python%20package/badge.svg) https://readthedocs.org/projects/cpvlib/badge/?version=latest&style=plastic [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/isi-ies-group/cpvlib/blob/master/docs/examples/StaticHybridSystem_tmy.ipynb)

The `cpvlib` library is a layer over [`pvlib-python`](https://github.com/pvlib/pvlib-python) that models CPV systems.

It is built in file `cpvlib.py`, that contains the `cpvsystem` module with following classes:

* CPVSystem
* StaticCPVSystem
* StaticFlatPlateSystem
* StaticHybridSystem

<img src="docs/source/_images/cpvlib_schema.png" width="600" alt="cpvlib classes schema">

A more detailed description can be found in the Documentation at [readthedocs](http://cpvlib.readthedocs.io).

## Library installation & usage

*Pre-release installation*
`pip install --force-reinstall --no-deps git+https://github.com/isi-ies-group/cpvlib.git`

`from cpvlib import cpvsystem`
`cpvsystem.StaticHybridSystem(...)`

## License

TBD

## Live Jupyter notebook demo
StaticHybridSystem_tmy.ipynb
<!---* Binder [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/isi-ies-group/cpvlib/master?filepath=docs/examples/StaticHybridSystem_tmy.ipynb)
--->
* Google Colab [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/isi-ies-group/cpvlib/blob/master/docs/examples/StaticHybridSystem_tmy.ipynb)

<!---
*Testing dataset* [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3346823.svg)](https://doi.org/10.5281/zenodo.3346823)
--->
