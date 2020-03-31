# cpvlib ![Python package](https://github.com/isi-ies-group/cpvlib/workflows/Python%20package/badge.svg)
Parte del trabajo de Marcos

Dataset de prueba [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3346823.svg)](https://doi.org/10.5281/zenodo.3346823)

## Notebooks en Binder
* prueba_cpvlib.ipynb [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/isi-ies-group/cpvlib/master?urlpath=lab?filepath=prueba_cpvlib.ipynb)
* determinacion_iam.ipynb [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/isi-ies-group/cpvlib/master?urlpath=lab?filepath=determinacion_iam.ipynb)

## TO DO
* [x] StaticCPVSystem debe heredar de verdad de CPVSystem
* [x] Usar nombre "hybrid" para el sistema entero, no para el sistema de difusa
* [x] Generar dii directamente desde el método StaticCPVSystem.get_irradiance()
* [ ] Ejecutar los UFs internamente en StaticCPVSystem
* [x] Renombrar dict UF_parameters a notación de Marcos
* [ ] Auto rellenar los parámetros de UF desde self.xxx para UF_DNI
* [ ] Contar efecto desuniformidad en células de base cuando DNI se suma a difusa
* [ ] Modelo térmico. Más allá de pvsyst_celltemp() ¿?
* [x] Usar nombre "hybrid" para el sistema entero, no para el sistema de difusa
* [x] Obtener funcion IAM
* [x] Cambiar UF_AOI por IAM
* [ ] Meter aoi_limit=55 en parametros del módulo
* [x] Escribir tests basados en dataset 2019-05
* [ ] Hacer más tests
* [ ] Upgrade a pvlib v0.8 -> Hay que usar pvlib.temperature.pvsyst_cell()
* [ ] Ver racking_model='open_rack_cell_glassback' en CPVSystem, ya que es del modelo 'sapm', pero usamo el 'pvsyst'
* [ ] Vigilar (test?) el paso de kwargs de los métodos de las clases
