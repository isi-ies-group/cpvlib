# cpvlib ![Python package](https://github.com/isi-ies-group/cpvlib/workflows/Python%20package/badge.svg)
Parte del trabajo de Marcos

Dataset de prueba [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3346823.svg)](https://doi.org/10.5281/zenodo.3346823)

## Notebooks en Binder
* yield_pv.ipynb [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/isi-ies-group/cpvlib/master?filepath=yield_pv.ipynb)
* yield_cpv.ipynb [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/isi-ies-group/cpvlib/master?filepath=yield_cpv.ipynb)
* yield_static_cpv.ipynb [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/isi-ies-group/cpvlib/master?filepath=yield_static_cpv.ipynb)
* yield_static_diffuse.ipynb [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/isi-ies-group/cpvlib/master?filepath=yield_static_diffuse.ipynb)

* prueba_tmy_HybridSystem.ipynb [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/isi-ies-group/cpvlib/master?urlpath=lab?filepath=prueba_tmy_HybridSystem.ipynb)

## TO DO
* [x] StaticCPVSystem debe heredar de verdad de CPVSystem
* [x] Usar nombre "hybrid" para el sistema entero, no para el sistema de difusa
* [x] Generar dii directamente desde el método StaticCPVSystem.get_irradiance()
* [x] Ejecutar los UFs internamente en StaticCPVSystem
* [x] Renombrar dict UF_parameters a notación de Marcos
* [ ] Auto rellenar los parámetros de UF desde self.xxx para UF_DNI
* [ ] Contar efecto desuniformidad en células de base cuando DNI se suma a difusa
* [ ] Modelo térmico. Más allá de pvsyst_celltemp() ¿?
* [x] Usar nombre "hybrid" para el sistema entero, no para el sistema de difusa
* [x] Obtener funcion IAM
* [x] Cambiar UF_AOI por IAM
* [ ] Meter aoi_limit=55 en parametros del módulo StaticDiffuseSystem
* [ ] Meter parámetro de IAM en parametros del módulo StaticCPVSystem
* [ ] Convertir funciones por tramos a tipo np.piecewise()
* [ ] Meter parámetro de UF_aoi_difusa en parametros del módulo
* [x] Escribir tests basados en dataset 2019-05
* [ ] Hacer más tests
* [ ] Upgrade a pvlib v0.8 -> Hay que usar pvlib.temperature.pvsyst_cell()
* [ ] Ver racking_model='open_rack_cell_glassback' en CPVSystem, ya que es del modelo 'sapm', pero usamo el 'pvsyst'
* [ ] Vigilar (test?) el paso de kwargs de los métodos de las clases

* [x] Extraer parámetros de sistema difusa. Ver UF: luz que no llega.
* [ ] Aplicar UF_difusa a sistema Hybrid
* [x] Ajustar módulos CPV (Fadrique e Intrepido) con modelos térmicos Sandia (a, b) y PVSyst
* [ ] Ver Voc de silicio como indicador de tcell. Como 1ª aprox. tomamos GII como radiación de entrada.
        Hay más temperatura de célula: Modelo radiación difusa + directa
* [x] Que medimos? Para utilizar medidas de ahora. Preguntar a Steve ->
        carpeta 'inso_mod': Solo un módulo (29) tiene corriente difusa y es 0.1 A (/10 esperado)
* [ ] Ajustar parametros de parte difusa y tracker
* [x] Añadir tracker a StaticCPVSystem
* [x] Repasar get_aoi() CPVSystem y get_irradiance()
* [ ] Renombrar in_tracker a in_singleaxistracker
* [ ] Repasar atributo albedo
* [ ] Limitar AOI con aoi_limit en StaticCPVSystem.get_iam() ¿? Ahora supera los 55º
* [ ] Cual sería la reference_irradiance de StaticDiffuseSystem ¿dhi, ghi, la get_irradiance(aoi_limit)?