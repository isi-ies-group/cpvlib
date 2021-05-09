# cpvlib
![Python package](https://github.com/isi-ies-group/cpvlib/workflows/Python%20package/badge.svg)
<a href="http://cpvlib.readthedocs.org/">
  <img src="https://readthedocs.org/projects/cpvlib/badge/?style=plastic" alt="RTD doc" />
</a>

<img src="docs/source/_images/cpvlib_logo.png" width="800" alt="cpvlib logo">

`cpvlib` is a python package for modeling CPV systems built as a layer over [`pvlib-python`](https://github.com/pvlib/pvlib-python).

It is built in file `cpvlib.py`, that contains the `cpvsystem` module with following classes:

* CPVSystem
* StaticCPVSystem
* StaticFlatPlateSystem
* StaticHybridSystem

<img src="docs/source/_images/cpvlib_mods.png" width="800" alt="cpvlib classes">
<img src="docs/source/_images/cpvlib_schema.png" width="800" alt="cpvlib classes schema">

A more detailed description can be found in the Documentation at [readthedocs](http://cpvlib.readthedocs.io).

## Library installation & usage

*Installation from source*
`pip install --force-reinstall --no-deps git+https://github.com/isi-ies-group/cpvlib.git`

`from cpvlib import cpvsystem`
`cpvsystem.StaticHybridSystem(...)`

## Contributing

Please see the [Contributing page](http://cpvlib.readthedocs.io/en/latest/contributing.html) for more on how you can contribute.
 
## License

TBD

## Getting support

If you suspect that you may have discovered a bug or if you'd like to
change something about cpvlib, then please make an issue on the
[GitHub issues page](https://github.com/isi-ies-group/issues).

## Live Jupyter notebook demo
StaticHybridSystem_tmy.ipynb
<!---* Binder [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/isi-ies-group/cpvlib/master?filepath=docs/examples/StaticHybridSystem_tmy.ipynb)
--->
* Google Colab [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/isi-ies-group/cpvlib/blob/master/docs/examples/StaticHybridSystem_tmy.ipynb)

<!---
*Testing dataset* [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3346823.svg)](https://doi.org/10.5281/zenodo.3346823)
--->
