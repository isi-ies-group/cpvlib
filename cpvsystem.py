"""
The ``cpvsystem`` module contains functions for modeling the output and
performance of CPV modules.
"""

import pandas as pd

from pvlib import pvsystem
from pvlib.pvsystem import PVSystem
from pvlib import atmosphere, irradiance
from pvlib.tools import _build_kwargs


class CPVSystem(PVSystem):
    """
    The CPVSystem class defines a set of CPV system attributes and modeling
    functions. This class describes the collection and interactions of CPV
    system components installed on a Dual Axis Tracker.

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

    racking_model : None or string, default 'open_rack_cell_glassback'
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
                 modules_per_string=1, strings_per_inverter=1,
                 inverter=None, inverter_parameters=None,
                 racking_model='open_rack_cell_glassback',
                 losses_parameters=None, name=None, **kwargs):

        self.name = name

        # could tie these together with @property
        self.module = module
        if module_parameters is None:
            self.module_parameters = {}
        else:
            self.module_parameters = module_parameters

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
            dni_extra = irradiance.get_extra_radiation(solar_zenith.index)

        if airmass is None:
            airmass = atmosphere.get_relative_airmass(solar_zenith)

        return irradiance.get_total_irradiance(90 - solar_zenith,
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

        return pvsystem.pvsyst_celltemp(poa_global, temp_air, wind_speed,
                                        model_params=self.racking_model,
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
            inclination of the first regression line of the utilization factor
            for airmass.

        am_uf_m_high : numeric
            inclination of the second regression line of the utilization factor
            for airmass.

        Returns
        -------
        am_uf : numeric
            the utilization factor for airmass.
        """
        if am_thld is not None:
            return get_simple_util_factor(x=airmass, thld=am_thld,
                                          m_low=am_uf_m_low,
                                          m_high=am_uf_m_high)
        else:
            return get_simple_util_factor(x=airmass, thld=self.module_parameters['am_thld'],
                                          m_low=self.module_parameters['am_uf_m_low'] /
                                          self.module_parameters['IscDNI_top'],
                                          m_high=self.module_parameters['am_uf_m_high']/self.module_parameters['IscDNI_top'])

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
            inclination of the first regression line of the utilization factor
            for ambient temperature.

        ta_uf_m_high : numeric
            inclination of the second regression line of the utilization factor
            for ambient temperature.

        Returns
        -------
        ta_uf : numeric
            the utilization factor for ambient temperature.
        """
        if ta_thld is not None:
            return get_simple_util_factor(x=temp_air, thld=ta_thld,
                                          m_low=ta_uf_m_low,
                                          m_high=ta_uf_m_high)
        else:
            return get_simple_util_factor(x=temp_air, thld=self.module_parameters['ta_thld'],
                                          m_low=self.module_parameters['ta_uf_m_low'] /
                                          self.module_parameters['IscDNI_top'],
                                          m_high=self.module_parameters['ta_uf_m_high']/self.module_parameters['IscDNI_top'])

    def get_dni_util_factor(self, dni, dni_thld, dni_uf_m_low, dni_uf_m_high):
        """
        Retrieves the utilization factor for DNI.

        Parameters
        ----------
        dni : numeric
            Direct Normal Irradiance

        dni_thld : numeric
            limit between the two regression lines of the utilization factor.

        dni_uf_m_low : numeric
            inclination of the first regression line of the utilization factor
            for DNI.

        dni_uf_m_low_uf_m_high : numeric
            inclination of the second regression line of the utilization factor
            for DNI.

        Returns
        -------
        dni_uf : numeric
            the utilization factor for DNI.
        """

        return get_simple_util_factor(x=dni, thld=dni_thld,
                                      m_low=dni_uf_m_low,
                                      m_high=dni_uf_m_high)

    def get_global_utilization_factor(self, airmass_absolute, temp_air,
                                      solar_zenith, solar_azimuth):

        uf_am = self.get_am_util_factor(airmass=airmass_absolute)

        uf_ta = self.get_tempair_util_factor(temp_air=temp_air)

        uf_global = (uf_am * self.module_parameters['weight_am'] +
                    uf_ta * self.module_parameters['weight_temp'])

        return uf_global


class StaticCPVSystem(CPVSystem):
    """
    The StaticCPVSystem class defines a set of CPV system attributes and
    modeling functions. This class describes the collection and interactions of
    Static CPV system components installed on a Fixed Panel.

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

    racking_model : None or string, default 'open_rack_cell_glassback'
        Used for cell and module temperature calculations.

    losses_parameters : None, dict or Series, default None
        Losses parameters as defined by PVWatts or other.

    name : None or string, default None

    **kwargs
        Arbitrary keyword arguments.
        Included for compatibility, but not used.
    """

    def __init__(self,
                 surface_tilt=0, surface_azimuth=180,
                 module=None, module_parameters=None,
                 modules_per_string=1, strings_per_inverter=1,
                 inverter=None, inverter_parameters=None,
                 racking_model='open_rack_cell_glassback',
                 losses_parameters=None, name=None, **kwargs):

        self.surface_tilt = surface_tilt
        self.surface_azimuth = surface_azimuth

        super().__init__(module, module_parameters, modules_per_string,
                           strings_per_inverter, inverter, inverter_parameters,
                           racking_model, losses_parameters, name, **kwargs)

    def __repr__(self):
        attrs = ['name', 'module', 'inverter', 'racking_model']
        return ('StaticCPVSystem: \n  ' + '\n  '.join(
            ('{}: {}'.format(attr, getattr(self, attr)) for attr in attrs)))

    def get_irradiance(self, solar_zenith, solar_azimuth, dni, **kwargs):
        """
        Uses the :py:func:`irradiance.get_total_irradiance` function to
        calculate the plane of array irradiance components on a Fixed panel.

        Parameters
        ----------
        solar_zenith : float or Series.
            Solar zenith angle.
        solar_azimuth : float or Series.
            Solar azimuth angle.
        dni : float or Series
            Direct Normal Irradiance
        dhi : float or Series
            Diffuse horizontal irradiance
        **kwargs
            Passed to :func:`irradiance.total_irrad`.

        Returns
        -------
        poa_irradiance : DataFrame
            Column names are: ``total, beam, sky, ground``.
        """

        return irradiance.beam_component(
            self.surface_tilt,
            self.surface_azimuth,
            solar_zenith,
            solar_azimuth,
            dni,
            **kwargs)

    def get_aoi_util_factor(self, aoi, aoi_thld=None, aoi_uf_m_low=None, aoi_uf_m_high=None):
        """
        Retrieves the utilization factor for the Angle of Incidence.

        Parameters
        ----------
        aoi : numeric
            Angle of Incidence

        aoi_thld : numeric
            limit between the two regression lines of the utilization factor.

        aoi_uf_m_low : numeric
            inclination of the first regression line of the utilization factor
            for AOI.

        aoi_uf_m_low_uf_m_high : numeric
            inclination of the second regression line of the utilization factor
            for AOI.

        Returns
        -------
        aoi_uf : numeric
            the utilization factor for AOI.
        """
        if aoi_thld is not None:
            aoi_uf = get_simple_util_factor(x=aoi, thld=aoi_thld,
                                            m_low=aoi_uf_m_low,
                                            m_high=aoi_uf_m_high)
        else:
            aoi_uf = get_simple_util_factor(x=aoi, thld=self.module_parameters['aoi_thld'],
                                            m_low=self.module_parameters['aoi_uf_m_low'] /
                                            self.module_parameters['IscDNI_top'],
                                            m_high=self.module_parameters['aoi_uf_m_high']/self.module_parameters['IscDNI_top'])

        if isinstance(aoi_uf, (int, float)):
            if aoi_uf < 0:
                aoi_uf = 0
        else:
            # if aoi_uf < 0:
            #     return 0
            aoi_uf[aoi_uf < 0] = 0

        return aoi_uf

    def get_global_utilization_factor_con_aoi(self, airmass_absolute, temp_air,
                                      aoi, solar_zenith, solar_azimuth):

        uf_am = self.get_am_util_factor(airmass=airmass_absolute)

        uf_ta = self.get_tempair_util_factor(temp_air=temp_air)

        uf_am_at = (uf_am * self.module_parameters['weight_am'] +
                    uf_ta * self.module_parameters['weight_temp'])

        uf_aoi = self.get_aoi_util_factor(aoi=aoi)

        uf_aoi_ast = self.get_aoi_util_factor(aoi=0)

        uf_aoi_norm = uf_aoi / uf_aoi_ast

        uf_global = uf_am_at * uf_aoi_norm

        return uf_global
    
class StaticDiffuseSystem(PVSystem):
    
    def __init__(self,
                 surface_tilt=0, surface_azimuth=180,
                 module=None, module_parameters=None,
                 modules_per_string=1, strings_per_inverter=1,
                 inverter=None, inverter_parameters=None,
                 racking_model='open_rack_cell_glassback',
                 losses_parameters=None, name=None, **kwargs):
        
        super().__init__(surface_tilt=surface_tilt, surface_azimuth=surface_azimuth,
                 albedo=None, surface_type=None,
                 module=module, module_type='glass_polymer',
                 module_parameters=module_parameters,
                 temperature_model_parameters=None,
                 modules_per_string=modules_per_string, strings_per_inverter=strings_per_inverter,
                 inverter=inverter, inverter_parameters=inverter_parameters,
                 racking_model=racking_model, losses_parameters=losses_parameters, name=name,
                 **kwargs)

    def __repr__(self):
        attrs = ['name', 'module', 'inverter', 'racking_model']
        return ('StaticDiffuseSystem: \n  ' + '\n  '.join(
            ('{}: {}'.format(attr, getattr(self, attr)) for attr in attrs)))

    def get_irradiance(self, solar_zenith, solar_azimuth, aoi, aoi_limit, dni=None,
                       ghi=None, dhi=None, dii=None, gii=None, dni_extra=None,
                       airmass=None, model='haydavies', **kwargs):
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
        irradiation : DataFrame
        """

        # not needed for all models, but this is easier
        if dni_extra is None:
            dni_extra = irradiance.get_extra_radiation(solar_zenith.index)

        if airmass is None:
            airmass = atmosphere.get_relative_airmass(solar_zenith)

        if dii is None:
            dii = irradiance.beam_component(
                self.surface_tilt,
                self.surface_azimuth,
                solar_zenith,
                solar_azimuth,
                dni)

        if gii is None:
            irr = irradiance.get_total_irradiance(self.surface_tilt,
                                                  self.surface_azimuth,
                                                  solar_zenith, solar_azimuth,
                                                  dni, ghi, dhi,
                                                  dni_extra=dni_extra,
                                                  airmass=airmass,
                                                  model=model,
                                                  albedo=self.albedo,
                                                  **kwargs)

            poa_diffuse = irr['poa_sky_diffuse'] + irr['poa_ground_diffuse']
            gii = irr['poa_global']

        else:
            poa_diffuse = gii - dii
            
        poa_diffuse_static = pd.concat([poa_diffuse[aoi < aoi_limit], gii[aoi > aoi_limit]]).sort_index()

        return poa_diffuse_static

class StaticHybridSystem(object):
    
    def __init__(self,
                 surface_tilt=30,
                 surface_azimuth=180,
                 module_cpv=None,
                 module_parameters_cpv=None,
                 module_diffuse=None,
                 module_parameters_diffuse=None,
                 modules_per_string=1,
                 strings_per_inverter=1,
                 inverter=None,
                 inverter_parameters=None,
                 racking_model="insulated",
                 losses_parameters=None,
                 name=None,
                 **kwargs):
        
        self.name = name

        # could tie these together with @property
        self.module_cpv = module_cpv
        self.module_diffuse = module_diffuse
        
        if module_parameters_cpv is None:
            self.module_parameters_cpv = {}
        else:
            self.module_parameters_cpv = module_parameters_cpv
        
        if module_parameters_diffuse is None:
            self.module_parameters_diffuse = {}
        else:
            self.module_parameters_diffuse = module_parameters_diffuse

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
            modules_per_string=modules_per_string,
            strings_per_inverter=strings_per_inverter,
            inverter=inverter,
            inverter_parameters=inverter_parameters,
            racking_model=racking_model,
            losses_parameters=losses_parameters,
            name=name,
            )
        self.static_diffuse_sys = StaticDiffuseSystem(
            surface_tilt=surface_tilt,
            surface_azimuth=surface_azimuth,
            module=module_diffuse,
            module_parameters=module_parameters_diffuse,
            modules_per_string=modules_per_string,
            strings_per_inverter=strings_per_inverter,
            inverter=inverter,
            inverter_parameters=inverter_parameters,
            racking_model=racking_model,
            losses_parameters=losses_parameters,
            name=name,
            )

    def __repr__(self):
        attrs = ['name', 'module_cpv', 'module_diffuse', 'inverter', 'racking_model']
        return ('StaticHybridSystem: \n  ' + '\n  '.join(
            ('{}: {}'.format(attr, getattr(self, attr)) for attr in attrs)))

    def get_irradiance(self, solar_zenith, solar_azimuth, aoi, aoi_limit, dni=None,
                       ghi=None, dhi=None, dii=None, gii=None, dni_extra=None,
                       airmass=None, model='haydavies', **kwargs):
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
        irradiation : DataFrame
        """
        
        if dii is None:
            dii = self.static_cpv_sys.get_irradiance(solar_zenith, solar_azimuth, dni, **kwargs)
        
        poa_diffuse_static = self.static_diffuse_sys.get_irradiance(solar_zenith,
                                solar_azimuth,
                                aoi=aoi,
                                aoi_limit=aoi_limit,
                                dii=dii, # dii_effective no aplica, ya que si no el calculo de difusa es artificialmente alto!
                                gii=gii,
                                 **kwargs
                                )
        
        return dii, poa_diffuse_static

    def pvsyst_celltemp(self, dii, poa_diffuse_static, temp_air, wind_speed=1.0):
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
        
        celltemp_cpv = self.static_cpv_sys.pvsyst_celltemp(dii, temp_air, wind_speed,
                                        model_params=self.racking_model,
                                        **kwargs)
        
        celltemp_diffuse = self.static_diffuse_sys.pvsyst_celltemp(poa_diffuse_static, temp_air, wind_speed,
                                        model_params=self.racking_model,
                                        **kwargs)
        
        return celltemp_cpv, celltemp_diffuse
    
    def calcparams_pvsyst(self, dii, poa_diffuse_static, temp_cell):
        """
        Use the :py:func:`calcparams_pvsyst` function, the input
        parameters and ``self.module_parameters`` to calculate the
        module currents and resistances.

        Parameters
        ----------
        effective_irradiance : numeric
            The irradiance (W/m2) that is converted to photocurrent.

        temp_cell : float or Series
            The average cell temperature of cells within a module in C.

        Returns
        -------
        See pvsystem.calcparams_pvsyst for details
        """

        kwargs = _build_kwargs(['gamma_ref', 'mu_gamma', 'I_L_ref', 'I_o_ref',
                                'R_sh_ref', 'R_sh_0', 'R_sh_exp',
                                'R_s', 'alpha_sc', 'EgRef',
                                'irrad_ref', 'temp_ref',
                                'cells_in_series'],
                               self.module_parameters)

        diode_parameters_cpv = self.static_cpv_sys.calcparams_pvsyst(dii, temp_cell, **kwargs)
        diode_parameters_diffuse =  self.static_diffuse_sys.calcparams_pvsyst(poa_diffuse_static, temp_cell, **kwargs)

        return diode_parameters_cpv, diode_parameters_diffuse
    
    def singlediode(self, photocurrent, saturation_current,
                    resistance_series, resistance_shunt, nNsVth,
                    ivcurve_pnts=None):
        """Wrapper around the :py:func:`singlediode` function.

        Parameters
        ----------
        See pvsystem.singlediode for details

        Returns
        -------
        See pvsystem.singlediode for details
        """
        
        diode_parameters_cpv = self.static_cpv_sys.inglediode(photocurrent, saturation_current,
                           resistance_series, resistance_shunt, nNsVth,
                           ivcurve_pnts=ivcurve_pnts)
        diode_parameters_diffuse =  self.static_diffuse_sys.singlediode(photocurrent, saturation_current,
                           resistance_series, resistance_shunt, nNsVth,
                           ivcurve_pnts=ivcurve_pnts)
        
        return diode_parameters_cpv, diode_parameters_diffuse


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
        inclination of the first regression line of the utilization factor.

    m_high : numeric
        inclination of the second regression line of the utilization factor.

    Returns
    -------
    single_uf : numeric
        utilization factor for the x variable.
    """
    simple_uf = pd.Series()

    if isinstance(x, (int, float)):
        simple_uf = 1 + (x - thld) * m_low
#
#    else:
#        for index, value in x.items():
#            if value <= thld:
#                simple_uf.index = 1 + (value - thld) * m_low
#            else:
#                simple_uf.index = 1 + (value - thld) * m_high
    else:
        def f(value):
            if value <= thld:
                s = 1 + (value - thld) * m_low
            else:
                s = 1 + (value - thld) * m_high
            return s

        simple_uf = x.apply(f)

    return simple_uf
