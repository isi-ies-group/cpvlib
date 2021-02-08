"""
The ``cpvsystem`` module contains functions for modeling the output and
performance of CPV modules.
"""

import numpy as np
import pandas as pd

import pvlib
from pvlib.tools import _build_kwargs


class CPVSystem(pvlib.pvsystem.PVSystem):
    """
    The CPVSystem class defines a set of CPV system attributes and modeling
    functions. This class describes the collection and interactions of CPV
    system components installed on a Dual Axis Tracker.

    It inheritates from pvlib.pvsystem.PVSystem, modifying those methods that
    are specific for a CPV system following the PVSyst implementation.
    Besides, specific CPV utilization factors are added as defined in 
    https://doi.org/10.1063/1.3509185 as new methods and new specific CPV parameters
    are passes to these methods.

    The class supports basic system topologies consisting of:

        * `N` total modules arranged in series
          (`modules_per_string=N`, `strings_per_inverter=1`).
        * `M` total modules arranged in parallel
          (`modules_per_string=1`, `strings_per_inverter=M`).
        * `NxM` total modules arranged in `M` strings of `N` modules each
          (`modules_per_string=N`, `strings_per_inverter=M`).

    The attributes should generally be things that don't change about
    the system, such the type of module and the inverter. The instance
    methods accept arguments for things that do change, such as
    irradiance and temperature.

    Parameters
    ----------

    albedo : None or float, default None
        The ground albedo. If ``None``, will attempt to use
        ``surface_type`` and ``irradiance.SURFACE_ALBEDOS``
        to lookup albedo.

    surface_type : None or string, default None
        The ground surface type. See ``irradiance.SURFACE_ALBEDOS``
        for valid values.

    module : None or string, default None
        The model name of the modules.
        May be used to look up the module_parameters dictionary
        via some other method.

    module_parameters : None, dict or Series, default None
        Module parameters as defined by the SAPM, CEC, or other.

    modules_per_string: int or float, default 1
        See system topology discussion above.

    strings_per_inverter: int or float, default 1
        See system topology discussion above.

    inverter : None or string, default None
        The model name of the inverters.
        May be used to look up the inverter_parameters dictionary
        via some other method.

    inverter_parameters : None, dict or Series, default None
        Inverter parameters as defined by the SAPM, CEC, or other.

    racking_model : None or string, default 'freestanding'
        Used for cell and module temperature calculations.

    losses_parameters : None, dict or Series, default None
        Losses parameters as defined by PVWatts or other.

    name : None or string, default None

    **kwargs
        Arbitrary keyword arguments.
        Included for compatibility, but not used.
    """

    def __init__(self,
                 module=None, module_parameters=None,
                 temperature_model_parameters=None,
                 modules_per_string=1, strings_per_inverter=1,
                 inverter=None, inverter_parameters=None,
                 racking_model='freestanding',
                 losses_parameters=None, name=None, albedo=None,
                 surface_type=None, **kwargs):

        self.name = name

        self.module = module

        if module_parameters is None:
            self.module_parameters = {}
        else:
            self.module_parameters = module_parameters

        if temperature_model_parameters is None:
            self.temperature_model_parameters = {}
        else:
            self.temperature_model_parameters = temperature_model_parameters

        self.modules_per_string = modules_per_string
        self.strings_per_inverter = strings_per_inverter

        self.inverter = inverter
        if inverter_parameters is None:
            self.inverter_parameters = {}
        else:
            self.inverter_parameters = inverter_parameters

        if losses_parameters is None:
            self.losses_parameters = {}
        else:
            self.losses_parameters = losses_parameters

        self.racking_model = racking_model

        self.surface_type = surface_type
        if albedo is None:
            self.albedo = pvlib.irradiance.SURFACE_ALBEDOS.get(
                surface_type, 0.25)
        else:
            self.albedo = albedo

    def __repr__(self):
        attrs = ['name', 'module', 'inverter', 'racking_model']
        return ('CPVSystem: \n  ' + '\n  '.join(
            ('{}: {}'.format(attr, getattr(self, attr)) for attr in attrs)))

    def get_irradiance(self, solar_zenith, solar_azimuth, dni, ghi, dhi,
                       dni_extra=None, airmass=None, model='haydavies',
                       **kwargs):
        """
        Uses the :py:func:`irradiance.get_total_irradiance` function to
        calculate the plane of array irradiance components on a Dual axis
        tracker.

        Parameters
        ----------
        solar_zenith : float or Series.
            Solar zenith angle.
        solar_azimuth : float or Series.
            Solar azimuth angle.
        dni : float or Series
            Direct Normal Irradiance
        ghi : float or Series
            Global horizontal irradiance
        dhi : float or Series
            Diffuse horizontal irradiance
        dni_extra : None, float or Series, default None
            Extraterrestrial direct normal irradiance
        airmass : None, float or Series, default None
            Airmass
        model : String, default 'haydavies'
            Irradiance model.

        **kwargs
            Passed to :func:`irradiance.total_irrad`.

        Returns
        -------
        poa_irradiance : DataFrame
            Column names are: ``total, beam, sky, ground``.
        """

        # not needed for all models, but this is easier
        if dni_extra is None:
            dni_extra = pvlib.irradiance.get_extra_radiation(
                solar_zenith.index)

        if airmass is None:
            airmass = pvlib.atmosphere.get_relative_airmass(solar_zenith)

        return pvlib.irradiance.get_total_irradiance(90 - solar_zenith,
                                                     solar_azimuth,
                                                     solar_zenith, solar_azimuth,
                                                     dni, ghi, dhi,
                                                     dni_extra=dni_extra,
                                                     airmass=airmass,
                                                     model=model,
                                                     albedo=self.albedo,
                                                     **kwargs)

    def pvsyst_celltemp(self, poa_global, temp_air, wind_speed=1.0):
        """
        Uses :py:func:`pvsystem.pvsyst_celltemp` to calculate module
        temperatures based on ``self.racking_model`` and the input parameters.

        Parameters
        ----------
        See pvsystem.pvsyst_celltemp for details

        Returns
        -------
        See pvsystem.pvsyst_celltemp for details
        """

        kwargs = _build_kwargs(['eta_m', 'alpha_absorption'],
                               self.module_parameters)
        kwargs.update(_build_kwargs(['u_c', 'u_v'],
                                    self.temperature_model_parameters))

        return pvlib.temperature.pvsyst_cell(poa_global, temp_air, wind_speed,
                                             **kwargs)

    def get_am_util_factor(self, airmass, am_thld=None, am_uf_m_low=None, am_uf_m_high=None):
        """
        Retrieves the utilization factor for airmass.

        Parameters
        ----------
        airmass : numeric
            absolute airmass.

        am_thld : numeric
            limit between the two regression lines of the utilization factor.

        am_uf_m_low : numeric
            slope of the first regression line of the utilization factor
            for airmass.

        am_uf_m_high : numeric
            slope of the second regression line of the utilization factor
            for airmass.

        Returns
        -------
        am_uf : numeric
            the utilization factor for airmass.
        """
        if am_thld is not None:
            am_uf = get_simple_util_factor(x=airmass, thld=am_thld,
                                           m_low=am_uf_m_low,
                                           m_high=am_uf_m_high)
        else:
            am_uf = get_simple_util_factor(x=airmass, thld=self.module_parameters['am_thld'],
                                           m_low=self.module_parameters['am_uf_m_low'] /
                                           self.module_parameters['IscDNI_top'],
                                           m_high=self.module_parameters['am_uf_m_high']/self.module_parameters['IscDNI_top'])
        return am_uf

    def get_tempair_util_factor(self, temp_air, ta_thld=None, ta_uf_m_low=None,
                                ta_uf_m_high=None):
        """
        Retrieves the utilization factor for ambient temperature.

        Parameters
        ----------
        temp_air : numeric
            Ambient dry bulb temperature in degrees C.

        ta_thld : numeric
            limit between the two regression lines of the utilization factor.

        ta_uf_m_low : numeric
            slope of the first regression line of the utilization factor
            for ambient temperature.

        ta_uf_m_high : numeric
            slope of the second regression line of the utilization factor
            for ambient temperature.

        Returns
        -------
        ta_uf : numeric
            the utilization factor for ambient temperature.
        """
        if ta_thld is not None:
            ta_uf = get_simple_util_factor(x=temp_air, thld=ta_thld,
                                           m_low=ta_uf_m_low,
                                           m_high=ta_uf_m_high)
        else:
            ta_uf = get_simple_util_factor(x=temp_air, thld=self.module_parameters['ta_thld'],
                                           m_low=self.module_parameters['ta_uf_m_low'] /
                                           self.module_parameters['IscDNI_top'],
                                           m_high=self.module_parameters['ta_uf_m_high']/self.module_parameters['IscDNI_top'])
        return ta_uf

    def get_dni_util_factor(self, dni, dni_thld=None, dni_uf_m_low=None, dni_uf_m_high=None):
        """
        Retrieves the utilization factor for DNI.

        Parameters
        ----------
        dni : numeric
            Direct Normal Irradiance

        dni_thld : numeric
            limit between the two regression lines of the utilization factor.

        dni_uf_m_low : numeric
            slope of the first regression line of the utilization factor
            for DNI.

        dni_uf_m_low_uf_m_high : numeric
            slope of the second regression line of the utilization factor
            for DNI.

        Returns
        -------
        dni_uf : numeric
            the utilization factor for DNI.
        """

        if dni_thld is not None:
            dni_uf = get_simple_util_factor(x=dni, thld=dni_thld,
                                            m_low=dni_uf_m_low,
                                            m_high=dni_uf_m_high)
        else:
            dni_uf = get_simple_util_factor(x=dni, thld=self.module_parameters['dni_thld'],
                                            m_low=self.module_parameters['dni_uf_m_low'] /
                                            self.module_parameters['IscDNI_top'],
                                            m_high=self.module_parameters['dni_uf_m_high']/self.module_parameters['IscDNI_top'])

        return dni_uf

    def get_global_utilization_factor(self, airmass_absolute, temp_air):
        """
        Retrieves the global utilization factor (Air mass and Air temperature CPV effects)

        Parameters
        ----------
        airmass : numeric
            absolute airmass.
        temp_air : numeric
            Ambient dry bulb temperature in degrees C.
            
        Returns
        -------
        uf_global : numeric
            the global utilization factor.
        """
        uf_am = self.get_am_util_factor(airmass=airmass_absolute)

        uf_ta = self.get_tempair_util_factor(temp_air=temp_air)

        uf_global = (uf_am * self.module_parameters['weight_am'] +
                     uf_ta * self.module_parameters['weight_temp'])

        return uf_global


class StaticCPVSystem(CPVSystem):
    """
    The StaticCPVSystem class defines a set of Static CPV system attributes and
    modeling functions. This class describes the collection and interactions of
    Static CPV system components installed on a Fixed Panel or a Single Axis tracker.

    It inheritates from CPVSystem, modifying those methods that
    are specific for a Static CPV system following the PVSyst implementation.

    The class supports basic system topologies consisting of:

        * `N` total modules arranged in series
          (`modules_per_string=N`, `strings_per_inverter=1`).
        * `M` total modules arranged in parallel
          (`modules_per_string=1`, `strings_per_inverter=M`).
        * `NxM` total modules arranged in `M` strings of `N` modules each
          (`modules_per_string=N`, `strings_per_inverter=M`).

    The attributes should generally be things that don't change about
    the system, such the type of module and the inverter. The instance
    methods accept arguments for things that do change, such as
    irradiance and temperature.

    Parameters
    ----------
    surface_tilt: float or array-like, default 0
        Surface tilt angles in decimal degrees.
        The tilt angle is defined as degrees from horizontal
        (e.g. surface facing up = 0, surface facing horizon = 90)

    surface_azimuth: float or array-like, default 180
        Azimuth angle of the module surface.
        North=0, East=90, South=180, West=270.

    module : None or string, default None
        The model name of the modules.
        May be used to look up the module_parameters dictionary
        via some other method.

    module_parameters : None, dict or Series, default None
        Module parameters as defined by the SAPM, CEC, or other.

    modules_per_string: int or float, default 1
        See system topology discussion above.

    strings_per_inverter: int or float, default 1
        See system topology discussion above.

    inverter : None or string, default None
        The model name of the inverters.
        May be used to look up the inverter_parameters dictionary
        via some other method.

    inverter_parameters : None, dict or Series, default None
        Inverter parameters as defined by the SAPM, CEC, or other.

    racking_model : None or string, default 'freestanding'
        Used for cell and module temperature calculations.

    losses_parameters : None, dict or Series, default None
        Losses parameters as defined by PVWatts or other.

    in_singleaxis_tracker : None or bool, defult False
        Conttros if the system is mounted in a NS single axis tracker
        If true, it affects get_aoi() and get_irradiance()

    name : None or string, default None

    **kwargs
        Arbitrary keyword arguments.
        Included for compatibility, but not used.
    """

    def __init__(self,
                 surface_tilt=0, surface_azimuth=180,
                 module=None, module_parameters=None,
                 temperature_model_parameters=None,
                 in_singleaxis_tracker=False,
                 b=None,
                 parameters_tracker=None,
                 modules_per_string=1, strings_per_inverter=1,
                 inverter=None, inverter_parameters=None,
                 racking_model='freestanding',
                 losses_parameters=None, name=None, **kwargs):

        self.surface_tilt = surface_tilt
        self.surface_azimuth = surface_azimuth

        self.in_singleaxis_tracker = in_singleaxis_tracker

        if parameters_tracker is None:
            self.parameters_tracker = {}
        else:
            self.parameters_tracker = parameters_tracker

        super().__init__(module, module_parameters, temperature_model_parameters, modules_per_string,
                         strings_per_inverter, inverter, inverter_parameters,
                         racking_model, losses_parameters, name, **kwargs)

    def __repr__(self):
        attrs = ['name', 'module', 'inverter', 'racking_model']
        return ('StaticCPVSystem: \n  ' + '\n  '.join(
            ('{}: {}'.format(attr, getattr(self, attr)) for attr in attrs)))

    def get_aoi(self, solar_zenith, solar_azimuth):
        """Get the angle of incidence on the system.

        Parameters
        ----------
        solar_zenith : float or Series.
            Solar zenith angle.
        solar_azimuth : float or Series.
            Solar azimuth angle.

        Returns
        -------
        aoi : Series
            The angle of incidence
        """
        if self.in_singleaxis_tracker:
            aoi = pvlib.tracking.singleaxis(
                solar_zenith, solar_azimuth, **self.parameters_tracker).aoi
        else:
            aoi = pvlib.irradiance.aoi(self.surface_tilt, self.surface_azimuth,
                                       solar_zenith, solar_azimuth)
        return aoi

    def get_iam(self, aoi, iam_model):
        """
        Determine the incidence angle modifier using the method specified by
        ``iam_model``.

        Parameters for the selected IAM model are expected to be in
        ``StaticCPVSystem.module_parameters``.

        Parameters
        ----------
        aoi : numeric
            The angle of incidence in degrees.

        aoi_model : string
            The IAM model to be used. Valid strings are 'ashrae' and 'interp'.

        Returns
        -------
        iam : numeric
            The AOI modifier.

        Raises
        ------
        AttributeError if `b` for 'ashrae' or `theta_ref` or `iam_red` for 'interp' are missing
        ValueError if `iam_model` is not a valid model name.
        """

        if iam_model == 'ashrae':
            if self.module_parameters['b'] is None:
                raise AttributeError(
                    'Missing IAM parameter (ASHRAE:b) in "module_parameters"')
            else:
                iam = pvlib.iam.ashrae(aoi, b=self.module_parameters['b'])
        elif iam_model == 'interp':
            if self.module_parameters['theta_ref'] is None or self.module_parameters['iam_ref'] is None:
                raise AttributeError(
                    'Missing IAM parameter (interp:theta_ref or iam_red) in "module_parameters"')
            else:
                iam = pvlib.iam.interp(
                    aoi, self.module_parameters['theta_ref'], self.module_parameters['iam_ref'], method='linear')
        else:
            raise ValueError(iam_model + ' is not a valid IAM model')

        return iam

    def get_irradiance(self, solar_zenith, solar_azimuth, dni):
        """
        Uses the :py:func:`pvlib.irradiance.beam_component` function to
        calculate the beam component of the plane of array irradiance.

        Parameters
        ----------
        solar_zenith : float or Series.
            Solar zenith angle.
        solar_azimuth : float or Series.
            Solar azimuth angle.
        dni : float or Series
            Direct Normal Irradiance

        Returns
        -------
        dii : numeric
            Direct (on the) Inclinated (plane) Irradiance
            Beam component of the plane of array irradiance
        """

        if self.in_singleaxis_tracker:
            tracking_info = pvlib.tracking.singleaxis(
                solar_zenith, solar_azimuth, **self.parameters_tracker)

            surface_tilt = tracking_info.surface_tilt
            surface_azimuth = tracking_info.surface_azimuth
        else:
            surface_tilt = self.surface_tilt
            surface_azimuth = self.surface_azimuth

        dii = pvlib.irradiance.beam_component(
            surface_tilt,
            surface_azimuth,
            solar_zenith,
            solar_azimuth,
            dni)

        return dii

    def get_effective_irradiance(self, solar_zenith, solar_azimuth, dni):
        """
        Calculates the effective irradiance (taking into account the IAM)

        Parameters
        ----------
        solar_zenith : float or Series
            Solar zenith angle.
        solar_azimuth : float or Series
            Solar azimuth angle.
        dni : float or Series
            Direct Normal Irradiance

        Returns
        -------
        dii_effective : float or Series
            Effective Direct (on the) Inclinated (plane) Irradiance
            Beam component of the plane of array irradiance plus the effect of AOI
        """

        dii = self.get_irradiance(solar_zenith, solar_azimuth, dni)

        aoi = self.get_aoi(solar_zenith, solar_azimuth)

        dii_effective = dii * \
            self.get_iam(aoi, iam_model=self.module_parameters['iam_model'])

        return dii_effective


class StaticFlatPlateSystem(pvlib.pvsystem.PVSystem):
    """
    The StaticFlatPlateSystem class defines a set of Static FlatPlate system attributes and
    modeling functions. This class describes the collection and interactions of
    Static FlatPlate system components installed on a Fixed Panel or a Single Axis tracker.

    It inheritates from PVSystem, modifying those methods that
    are specific for a Static FlatPlate system following the PVSyst implementation.

    The class supports basic system topologies consisting of:

        * `N` total modules arranged in series
          (`modules_per_string=N`, `strings_per_inverter=1`).
        * `M` total modules arranged in parallel
          (`modules_per_string=1`, `strings_per_inverter=M`).
        * `NxM` total modules arranged in `M` strings of `N` modules each
          (`modules_per_string=N`, `strings_per_inverter=M`).

    The attributes should generally be things that don't change about
    the system, such the type of module and the inverter. The instance
    methods accept arguments for things that do change, such as
    irradiance and temperature.

    Parameters
    ----------
    surface_tilt: float or array-like, default 0
        Surface tilt angles in decimal degrees.
        The tilt angle is defined as degrees from horizontal
        (e.g. surface facing up = 0, surface facing horizon = 90)

    surface_azimuth: float or array-like, default 180
        Azimuth angle of the module surface.
        North=0, East=90, South=180, West=270.

    module : None or string, default None
        The model name of the modules.
        May be used to look up the module_parameters dictionary
        via some other method.

    module_parameters : None, dict or Series, default None
        Module parameters as defined by the SAPM, CEC, or other.

    modules_per_string: int or float, default 1
        See system topology discussion above.

    strings_per_inverter: int or float, default 1
        See system topology discussion above.

    inverter : None or string, default None
        The model name of the inverters.
        May be used to look up the inverter_parameters dictionary
        via some other method.

    inverter_parameters : None, dict or Series, default None
        Inverter parameters as defined by the SAPM, CEC, or other.

    racking_model : None or string, default 'freestanding'
        Used for cell and module temperature calculations.

    losses_parameters : None, dict or Series, default None
        Losses parameters as defined by PVWatts or other.

    in_singleaxis_tracker : None or bool, defult False
        Conttros if the system is mounted in a NS single axis tracker
        If true, it affects get_aoi() and get_irradiance()

    name : None or string, default None

    **kwargs
        Arbitrary keyword arguments.
        Included for compatibility, but not used.
    """

    def __init__(self,
                 surface_tilt=0, surface_azimuth=180,
                 module=None, module_parameters=None,
                 temperature_model_parameters=None,
                 modules_per_string=1,
                 in_singleaxis_tracker=False,
                 parameters_tracker=None,
                 strings_per_inverter=1,
                 inverter=None, inverter_parameters=None,
                 racking_model='freestanding',
                 losses_parameters=None, name=None, **kwargs):

        self.in_singleaxis_tracker = in_singleaxis_tracker

        if parameters_tracker is None:
            self.parameters_tracker = {}
        else:
            self.parameters_tracker = parameters_tracker

        super().__init__(surface_tilt=surface_tilt, surface_azimuth=surface_azimuth,
                         albedo=None, surface_type=None,
                         module=module, module_type='glass_polymer',
                         module_parameters=module_parameters,
                         temperature_model_parameters=temperature_model_parameters,
                         modules_per_string=modules_per_string, strings_per_inverter=strings_per_inverter,
                         inverter=inverter, inverter_parameters=inverter_parameters,
                         racking_model=racking_model, losses_parameters=losses_parameters, name=name,
                         **kwargs)

    def __repr__(self):
        attrs = ['name', 'module', 'inverter', 'racking_model']
        return ('StaticFlatPlateSystem: \n  ' + '\n  '.join(
            ('{}: {}'.format(attr, getattr(self, attr)) for attr in attrs)))

    def get_aoi(self, solar_zenith, solar_azimuth):
        """Get the angle of incidence on the system.

        Parameters
        ----------
        solar_zenith : float or Series.
            Solar zenith angle.
        solar_azimuth : float or Series.
            Solar azimuth angle.

        Returns
        -------
        aoi : Series
            The angle of incidence
        """
        if self.in_singleaxis_tracker:
            aoi = pvlib.tracking.singleaxis(
                solar_zenith, solar_azimuth, **self.parameters_tracker).aoi
        else:
            aoi = pvlib.irradiance.aoi(self.surface_tilt, self.surface_azimuth,
                                       solar_zenith, solar_azimuth)
        return aoi

    def get_iam(self, aoi, aoi_thld, m1, b1, m2, b2):
        """
        Determines the angle of incidence modifier using a two-step piecewise regression function.
        TO BE VALIDATED

        Parameters
        ----------
        aoi : numeric
            The angle of incidence in degrees.

        aoi_thld : numeric
            limit between the two regression lines of the IAM.

        m1 : numeric
            slope of the first regression line of the IAM.

        b1 : numeric
            intercept of the first regression line of the IAM.

        m2 : numeric
            slope of the second regression line of the IAM.

        b2 : numeric
            intercept of the first regression line of the IAM.

        Returns
        -------
        iam : numeric
            The AOI modifier.

        """
        if isinstance(aoi, (int, float)):
            aoi_values = float(aoi)
        else:
            aoi_values = aoi.values

        if 'aoi_limit' in self.module_parameters:
            aoi_limit = self.module_parameters['aoi_limit']
        else:
            raise AttributeError(
                'Missing "aoi_limit" parameter in "module_parameters"')

        condlist = [aoi_values < aoi_limit,
                    (aoi_limit <= aoi_values) & (aoi_values < aoi_thld)]
        funclist = [lambda x:x*m1+b1, lambda x:x*m2+b2]

        if isinstance(aoi, (int, float)):
            iam = np.piecewise(aoi, condlist, funclist)
        else:
            iam = pd.Series(np.piecewise(
                aoi_values, condlist, funclist), index=aoi.index)

        return iam

    def get_irradiance(self, solar_zenith, solar_azimuth, dni=None,
                       ghi=None, dhi=None, dii=None, gii=None, dni_extra=None,
                       airmass=None, model='haydavies', spillage=0, **kwargs):
        """
        Calculates the plane of array irradiance of a Static Flat Plate system
        from dii and gii. If any is missing then is calculated from ghi, dhi and dhi
        using corresponding pvlib function.
        
        Internal `aoi_limit` parameter from `module_parameters` sets the limit
        of tracking of the Static CPV system and therefore when the dii irradiance
        is added to the poa_diffuse.
        
        Spillage factor accounts for the dii fraction that is allowed to pass into the system
        
        See https://doi.org/10.1002/pip.3387 for details

        Parameters
        ----------
        solar_zenith : float or Series.
            Solar zenith angle.
        solar_azimuth : float or Series.
            Solar azimuth angle.
        dni : numeric
            Direct Normal Irradiance
        ghi : numeric
            Global horizontal irradiance
        dhi : numeric
            Diffuse horizontal irradiance
        dii : numeric
            Direct (on the) Inclinated (plane) Irradiance
        gii : numeric
            Global (on the) Inclinated (plane) Irradiance
        dni_extra : None or numeric, default None
            Extraterrestrial direct normal irradiance
        airmass : None or numeric, default None
            Airmass
        model : String, default 'isotropic'
            Irradiance model.
        spillage : float
            Percentage of dii allowed to pass into the system

        Returns
        -------
        poa_flatplate_static : numeric
            Plane of Array Irradiance
        """

        # not needed for all models, but this is easier
        if dni_extra is None:
            dni_extra = pvlib.irradiance.get_extra_radiation(
                solar_zenith.index)

        if airmass is None:
            airmass = pvlib.atmosphere.get_relative_airmass(solar_zenith)

        if self.in_singleaxis_tracker:
            tracking_info = pvlib.tracking.singleaxis(
                solar_zenith, solar_azimuth, **self.parameters_tracker)

            surface_tilt = tracking_info.surface_tilt
            surface_azimuth = tracking_info.surface_azimuth
        else:
            surface_tilt = self.surface_tilt
            surface_azimuth = self.surface_azimuth

        if dii is None:
            dii = pvlib.irradiance.beam_component(
                surface_tilt,
                surface_azimuth,
                solar_zenith,
                solar_azimuth,
                dni)

        if gii is None:
            irr = pvlib.irradiance.get_total_irradiance(surface_tilt,
                                                        surface_azimuth,
                                                        solar_zenith, solar_azimuth,
                                                        dni, ghi, dhi,
                                                        dni_extra=dni_extra,
                                                        airmass=airmass,
                                                        model=model,
                                                        albedo=self.albedo,
                                                        **kwargs)

            poa_diffuse = irr['poa_diffuse']
            gii = irr['poa_global']

        else:
            poa_diffuse = gii - dii

        poa_diffuse += dii * spillage

        aoi = self.get_aoi(solar_zenith, solar_azimuth)

        if 'aoi_limit' in self.module_parameters:
            aoi_limit = self.module_parameters['aoi_limit']
        else:
            raise AttributeError(
                'Missing "aoi_limit" parameter in "module_parameters"')

        poa_flatplate_static = pd.concat(
            [poa_diffuse[aoi < aoi_limit], gii[aoi > aoi_limit]]).sort_index()

        return poa_flatplate_static

    def get_effective_irradiance(self, solar_zenith, solar_azimuth, dni=None,
                                 ghi=None, dhi=None, dii=None, gii=None, dni_extra=None,
                                 airmass=None, model='haydavies', spillage=0, aoi_thld=None, **kwargs):
        """
        Calculates the effective irradiance (taking into account the IAM)
        TO BE VALIDATED

        Parameters
        ----------
        solar_zenith : float or Series
            Solar zenith angle.
        solar_azimuth : float or Series
            Solar azimuth angle.
        dni : float or Series
            Direct Normal Irradiance

        Returns
        -------
        poa_flatplate_static_effective : float or Series
            Effective Direct (on the) Inclinated (plane) Irradiance
            Plane of array irradiance plus the effect of AOI
        """

        poa_flatplate_static = self.get_irradiance(solar_zenith, solar_azimuth, dni=dni,
                                                   ghi=ghi, dhi=dhi, dii=dii, gii=gii, dni_extra=dni_extra,
                                                   airmass=airmass, model=model, spillage=spillage, **kwargs)

        # * self.get_iam(
        poa_flatplate_static_effective = poa_flatplate_static
        # aoi=aoi, aoi_thld=aoi_thld, m1=1, b1=0, m2=1, b2=0)

        return poa_flatplate_static_effective

    def pvsyst_celltemp(self, poa_flatplate_static, temp_air, wind_speed=1.0):
        """
        Uses :py:func:`pvsystem.pvsyst_celltemp` to calculate module
        temperatures based on ``self.racking_model`` and the input parameters.

        Parameters
        ----------
        See pvsystem.pvsyst_celltemp for details

        Returns
        -------
        See pvsystem.pvsyst_celltemp for details
        """

        kwargs = _build_kwargs(['eta_m', 'alpha_absorption'],
                               self.module_parameters)
        kwargs.update(_build_kwargs(['u_c', 'u_v'],
                                    self.temperature_model_parameters))

        return pvlib.temperature.pvsyst_cell(poa_flatplate_static, temp_air, wind_speed,
                                             **kwargs)


class StaticHybridSystem():
    """
    The StaticHybridSystem class defines a set of Static Hybrid system attributes and
    modeling functions. This class describes the collection and interactions of
    Static CPV system components installed on a Fixed Panel or a Single Axis tracker.

    It is the composition of two subsystems: StaticCPVSystem and StaticFlatPlateSystem

    The class supports basic system topologies consisting of:

        * `N` total modules arranged in series
          (`modules_per_string=N`, `strings_per_inverter=1`).
        * `M` total modules arranged in parallel
          (`modules_per_string=1`, `strings_per_inverter=M`).
        * `NxM` total modules arranged in `M` strings of `N` modules each
          (`modules_per_string=N`, `strings_per_inverter=M`).

    The attributes should generally be things that don't change about
    the system, such the type of module and the inverter. The instance
    methods accept arguments for things that do change, such as
    irradiance and temperature.
    
    See https://doi.org/10.1002/pip.3387

    Parameters
    ----------
    surface_tilt: float or array-like, default 0
        Surface tilt angles in decimal degrees.
        The tilt angle is defined as degrees from horizontal
        (e.g. surface facing up = 0, surface facing horizon = 90)

    surface_azimuth: float or array-like, default 180
        Azimuth angle of the module surface.
        North=0, East=90, South=180, West=270.

    module : None or string, default None
        The model name of the modules.
        May be used to look up the module_parameters dictionary
        via some other method.

    module_parameters : None, dict or Series, default None
        Module parameters as defined by the SAPM, CEC, or other.

    modules_per_string: int or float, default 1
        See system topology discussion above.

    strings_per_inverter: int or float, default 1
        See system topology discussion above.

    inverter : None or string, default None
        The model name of the inverters.
        May be used to look up the inverter_parameters dictionary
        via some other method.

    inverter_parameters : None, dict or Series, default None
        Inverter parameters as defined by the SAPM, CEC, or other.

    racking_model : None or string, default 'freestanding'
        Used for cell and module temperature calculations.

    losses_parameters : None, dict or Series, default None
        Losses parameters as defined by PVWatts or other.

    in_singleaxis_tracker : None or bool, defult False
        Conttros if the system is mounted in a NS single axis tracker
        If true, it affects get_aoi() and get_irradiance()

    name : None or string, default None

    **kwargs
        Arbitrary keyword arguments.
        Included for compatibility, but not used.
    """
    def __init__(self,
                 surface_tilt=30,
                 surface_azimuth=180,
                 module_cpv=None,
                 module_parameters_cpv=None,
                 temperature_model_parameters_cpv=None,
                 module_flatplate=None,
                 module_parameters_flatplate=None,
                 temperature_model_parameters_flatplate=None,
                 in_singleaxis_tracker=False,
                 parameters_tracker=None,
                 modules_per_string=1,
                 strings_per_inverter=1,
                 inverter=None,
                 inverter_parameters=None,
                 racking_model="insulated",
                 losses_parameters=None,
                 name=None,
                 **kwargs):

        self.name = name

        self.surface_tilt = surface_tilt
        self.surface_azimuth = surface_azimuth

        # could tie these together with @property
        self.module_cpv = module_cpv
        self.module_flatplate = module_flatplate

        self.in_singleaxis_tracker = in_singleaxis_tracker

        if module_parameters_cpv is None:
            self.module_parameters_cpv = {}
        else:
            self.module_parameters_cpv = module_parameters_cpv

        if module_parameters_flatplate is None:
            self.module_parameters_flatplate = {}
        else:
            self.module_parameters_flatplate = module_parameters_flatplate

        if parameters_tracker is None:
            self.parameters_tracker = {}
        else:
            self.parameters_tracker = parameters_tracker

        self.modules_per_string = modules_per_string
        self.strings_per_inverter = strings_per_inverter

        self.inverter = inverter
        if inverter_parameters is None:
            self.inverter_parameters = {}
        else:
            self.inverter_parameters = inverter_parameters

        if losses_parameters is None:
            self.losses_parameters = {}
        else:
            self.losses_parameters = losses_parameters

        self.racking_model = racking_model

        self.static_cpv_sys = StaticCPVSystem(
            surface_tilt=surface_tilt,
            surface_azimuth=surface_azimuth,
            module=module_cpv,
            module_parameters=module_parameters_cpv,
            temperature_model_parameters=temperature_model_parameters_cpv,
            in_singleaxis_tracker=in_singleaxis_tracker,
            modules_per_string=modules_per_string,
            strings_per_inverter=strings_per_inverter,
            inverter=inverter,
            inverter_parameters=inverter_parameters,
            racking_model=racking_model,
            losses_parameters=losses_parameters,
            name=name,
        )

        self.static_flatplate_sys = StaticFlatPlateSystem(
            surface_tilt=surface_tilt,
            surface_azimuth=surface_azimuth,
            module=module_flatplate,
            module_parameters=module_parameters_flatplate,
            temperature_model_parameters=temperature_model_parameters_flatplate,
            in_singleaxis_tracker=in_singleaxis_tracker,
            modules_per_string=modules_per_string,
            strings_per_inverter=strings_per_inverter,
            inverter=inverter,
            inverter_parameters=inverter_parameters,
            racking_model=racking_model,
            losses_parameters=losses_parameters,
            name=name,
        )

    def __repr__(self):
        attrs = ['name', 'module_cpv', 'module_flatplate',
                 'inverter', 'racking_model']
        return ('StaticHybridSystem: \n  ' + '\n  '.join(
            ('{}: {}'.format(attr, getattr(self, attr)) for attr in attrs)))

    def get_effective_irradiance(self, solar_zenith, solar_azimuth, dni,
                                 ghi=None, dhi=None, dii=None, gii=None, dni_extra=None,
                                 airmass=None, model='haydavies', spillage=0, **kwargs):
        """
        Calculates the effective irradiance (taking into account the IAM)
        TO BE VALIDATED

        Parameters
        ----------
        solar_zenith : float or Series.
            Solar zenith angle.
        solar_azimuth : float or Series.
            Solar azimuth angle.
        dni : numeric
            Direct Normal Irradiance
        ghi : numeric
            Global horizontal irradiance
        dhi : numeric
            Diffuse horizontal irradiance
        dii : numeric
            Direct (on the) Inclinated (plane) Irradiance
        gii : numeric
            Global (on the) Inclinated (plane) Irradiance
        dni_extra : None or numeric, default None
            Extraterrestrial direct normal irradiance
        airmass : None or numeric, default None
            Airmass
        model : String, default 'isotropic'
            Irradiance model.
        spillage : float
            Percentage of dii allowed to pass into the system

        Returns
        -------
        dii_effective : float or Series
            Effective Direct (on the) Inclinated (plane) Irradiance [StaticCPVSystem]
            Beam component of the plane of array irradiance plus the effect of AOI
        poa_flatplate_static_effective : float or Series
            Effective Direct (on the) Inclinated (plane) Irradiance [StaticFlatPlateSystem]
            Plane of array irradiance plus the effect of AOI
        """

        dii_effective = self.static_cpv_sys.get_effective_irradiance(
            solar_zenith, solar_azimuth, dni)

        aoi = self.static_flatplate_sys.get_aoi(solar_zenith, solar_azimuth)

        poa_flatplate_static_effective = self.static_flatplate_sys.get_effective_irradiance(solar_zenith,
                                                                                            solar_azimuth,
                                                                                            aoi=aoi,
                                                                                            dii=dii,
                                                                                            gii=gii,
                                                                                            ghi=ghi,
                                                                                            dhi=dhi,
                                                                                            dni=dni,
                                                                                            model=model,
                                                                                            spillage=spillage,
                                                                                            **kwargs
                                                                                            )

        return dii_effective, poa_flatplate_static_effective

    def pvsyst_celltemp(self, dii, poa_flatplate_static, temp_air, wind_speed=1.0):
        """
        Uses :py:func:`pvsystem.pvsyst_celltemp` to calculate module
        temperatures based on ``self.racking_model`` and the input parameters.

        Parameters
        ----------
        dii : numeric
            Direct (on the) Inclinated (plane) Irradiance [StaticCPVSystem]
        poa_flatplate_static : numeric
            Plane of Array Irradiance [StaticFlatPlateSystem]
        
        See pvsystem.pvsyst_celltemp for details
            
        Returns
        -------
        See pvsystem.pvsyst_celltemp for details
        """

        celltemp_cpv = self.static_cpv_sys.pvsyst_celltemp(
            dii, temp_air, wind_speed)

        celltemp_flatplate = self.static_flatplate_sys.pvsyst_celltemp(
            poa_flatplate_static, temp_air, wind_speed)

        return celltemp_cpv, celltemp_flatplate

    def calcparams_pvsyst(self, dii, poa_flatplate_static, temp_cell_cpv, temp_cell_flatplate):
        """
        Use the :py:func:`calcparams_pvsyst` function, the input
        parameters and ``self.module_parameters`` to calculate the
        module currents and resistances.

        Parameters
        ----------
        dii : numeric
            Direct (on the) Inclinated (plane) Irradiance [StaticCPVSystem]
        poa_flatplate_static : numeric
            Plane of Array Irradiance [StaticFlatPlateSystem]

        temp_cell : float or Series
            The average cell temperature of cells within a module in C.

        Returns
        -------
        See pvsystem.calcparams_pvsyst for details
        """

        diode_parameters_cpv = self.static_cpv_sys.calcparams_pvsyst(
            dii, temp_cell_cpv)

        diode_parameters_flatplate = self.static_flatplate_sys.calcparams_pvsyst(
            poa_flatplate_static, temp_cell_flatplate)

        return diode_parameters_cpv, diode_parameters_flatplate

    def singlediode(self, diode_parameters_cpv, diode_parameters_flatplate, ivcurve_pnts=None):
        """Wrapper around the :py:func:`singlediode` function.

        Parameters
        ----------
        See pvsystem.singlediode for details [StaticCPVSystem & StaticFlatPlateSystem()]

        Returns
        -------
        See pvsystem.singlediode for details
        """

        dc_cpv = self.static_cpv_sys.singlediode(*diode_parameters_cpv,
                                                 ivcurve_pnts=ivcurve_pnts)

        dc_flatplate = self.static_flatplate_sys.singlediode(*diode_parameters_flatplate,
                                                             ivcurve_pnts=ivcurve_pnts)

        return dc_cpv, dc_flatplate

    def get_global_utilization_factor_cpv(self, airmass_absolute, temp_air):
        """
        Retrieves the global utilization factor (Air mass and Air temperature CPV effects)
        for the StaticCPVSystem subsystem

        Parameters
        ----------
        airmass : numeric
            absolute airmass.
        temp_air : numeric
            Ambient dry bulb temperature in degrees C.
            
        Returns
        -------
        uf_global : numeric
            the global utilization factor.
        """
        
        uf_am = self.static_cpv_sys.get_am_util_factor(
            airmass=airmass_absolute)

        uf_ta = self.static_cpv_sys.get_tempair_util_factor(temp_air=temp_air)

        uf_global = (uf_am * self.static_cpv_sys.module_parameters['weight_am'] +
                     uf_ta * self.static_cpv_sys.module_parameters['weight_temp'])

        return uf_global


def get_simple_util_factor(x, thld, m_low, m_high):
    """
    Retrieves the utilization factor for a variable.

    Parameters
    ----------
    x : numeric / pd.Series
        variable value(s) for the utilization factor calc.

    thld : numeric
        limit between the two regression lines of the utilization factor.

    m_low : numeric
        slope of the first regression line of the utilization factor.

    m_high : numeric
        slope of the second regression line of the utilization factor.

    Returns
    -------
    single_uf : numeric
        utilization factor for the x variable.
    """
    simple_uf = pd.Series(dtype='float64')

    if isinstance(x, (int, float)):
        simple_uf = 1 + (x - thld) * m_low

    else:
        def f(value):
            if value <= thld:
                s = 1 + (value - thld) * m_low
            else:
                s = 1 + (value - thld) * m_high
            return s

        simple_uf = x.apply(f)

    return simple_uf
