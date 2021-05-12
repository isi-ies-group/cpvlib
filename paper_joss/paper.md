---
title: '`cpvlib`: a python package for modeling CPV systems'
tags:
  - Python
  - solar energy
  - photovoltaics
  - CPV
  - renewable energy
authors:
  - name: Ruben Nuñez
    orcid: 0000-0001-9160-5416
    affiliation: "1,2"
  - name: Marcos Moreno
    orcid: 
    affiliation: 2
  - name: Cesar Dominguez
    orcid: 0000-0002-2751-7208
    affiliation: "1,2"
affiliations:
 - name: Instituto de Energía Solar, Universidad Politécnica de Madrid (IES-UPM)
   index: 1
 - name: Escuela Técnica Superior de Ingeniería y Diseño Industrial, Universidad Politécnica de Madrid
   index: 2

date: 15 May 2021
bibliography: paper.bib
---

# Statement of Need

`cpvlib` is an open source tool that provides a set of functions and classes 
for simulating the performance of concentrator photovoltaic (CPV) systems,
a specific type of photovoltiac systems composed of lenses and/or mirrors
that focus sunlight onto small cells. It places special emphasis on internally
tracked micro CPV systems, a promising line of research at present [@duerr_tracking_2011],
[@apostoleris_tracking-integrated_2016], [@dominguez_review_2017].

# Summary

`cpvlib` is constructed as a layer over pvlib-python [@pvlib_2018] to specifically
model CPV systems. Following pvlib-python structure, a module named `cpvsystem`
serves as recipient of the following classes:`CPVSystem` (on 2-axis tracker
CPV (sub)system), `StaticCPVSystem` (internal tracking CPV (sub)system),
`StaticFlatPlateSystem` (flat plate (sub)system) and `StaticHybridSystem` 
(hybrid static CPV+flat plate system). A graphical description of these
classes is given in \autoref{fig:classes}.
`cpvlib` is contributing to the growing ecosystem of open-source
tools for solar energy [@holmgren_review_2018].

![Schematic representation of the `cpvsystem` classes.\label{fig:classes}](cpvlib_mods.png){ width=80% }

`cpvlib`'s code is hosted on Github and it can be found on PyPi to be easily
installed with pip. It is licensed with a BSD 3-clause license allowing
permissive use with attribution and the documentation is hosted at readthedocs.org.
It is written in Python, and the code is structured with an object-oriented
approach. Continuous integration services allow for lint checking and to test
automation. Each class and function are documented with reference to the
literature when applicable.

Plans for `cpvlib` development includes the implementation of new
and existing models, addition of functionality to assist with
input/output, and improvements to API consistency.

Up to now `cpvlib` has been used to validate a micro CPV prototype, a
complete `StaticHybridSystem` as described in [@askins_performance_2019],
[@nardin_2020]. The campaign data used in this validation can be found in
[@askins_dataset_2019].
The project started as a final degree's thesis in 2019 and it has been
extended since then by the ISI-IES research group at UPM.

# Acknowledgements

This work has received funding from the European Union's Horizon
2020 research and innovation program under Grant Agreement
nº 857775 (project HIPERION) and under Grant Agreement nº 787289
(project GRECO).

# References
