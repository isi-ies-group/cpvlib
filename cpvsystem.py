"""
The ``cpvsystem`` module contains functions for modeling the output and
performance of CPV modules.
"""

import numpy as np
from collections import OrderedDict

from pvlib import pvsystem
from pvlib import atmosphere, irradiance
from pvlib.tools import _build_kwargs
from pvlib.location import Location

import math
from sklearn import linear_model
from sklearn.metrics import mean_squared_error


class CPVSystem(object):
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

    def calcparams_pvsyst(self, effective_irradiance, temp_cell):
        """
        Use the :py:func:`pvsystem.calcparams_pvsyst` function, the input
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

        return pvsystem.calcparams_pvsyst(effective_irradiance, 
                                          temp_cell, **kwargs)

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
 
    def singlediode(self, photocurrent, saturation_current,
                    resistance_series, resistance_shunt, nNsVth,
                    ivcurve_pnts=None):
        """Wrapper around the :py:func:`pvsystem.singlediode` function.

        Parameters
        ----------
        See pvsystem.singlediode for details

        Returns
        -------
        See pvsystem.singlediode for details
        """
        
        return pvsystem.singlediode(photocurrent, saturation_current, 
                                    resistance_series, resistance_shunt, 
                                    nNsVth, ivcurve_pnts=ivcurve_pnts)

    def get_am_util_factor(self, airmass, am_thld, am_uf_m_low, am_uf_m_high):
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
        
        return get_simple_util_factor(x = airmass, thld = am_thld, 
                                      m_low = am_uf_m_low,
                                      m_high = am_uf_m_high)
    
    def get_tempair_util_factor(self, temp_air, ta_thld, ta_uf_m_low, 
                                ta_uf_m_high):
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
        
        return get_simple_util_factor(x = temp_air, thld = ta_thld, 
                                      m_low = ta_uf_m_low,
                                      m_high = ta_uf_m_high)
    
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
                
        return get_simple_util_factor(x = dni, thld = dni_thld, 
                                      m_low = dni_uf_m_low,
                                      m_high = dni_uf_m_high)
    
    def get_utilization_factor(self, airmass, am_thld, am_uf_m_low, 
                               am_uf_m_high, am_weight, temp_air, ta_thld, 
                               ta_uf_m_low, ta_uf_m_high, ta_weight, dni, 
                               dni_thld, dni_uf_m_low, dni_uf_m_high, 
                               dni_weight):
        """
        Retrieves the unified utilization factor for airmass, ambient 
        temperature and dni.
        
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
            
        am_weight : numeric
            ponderation for the airmass utilization factor.
            
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
            
        ta_weight : numeric
            ponderation for the ambient temperature utilization factor.
            
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
            
        dni_weight : numeric
            ponderation for the DNI utilization factor.
        
        Returns
        -------
        uf : numeric
            global utilization factor.
        """
        
        am_uf = get_simple_util_factor(x = airmass, thld = am_thld, 
                                       m_low = am_uf_m_low,
                                       m_high = am_uf_m_high)
        
        ta_uf = get_simple_util_factor(x = temp_air, thld = ta_thld, 
                                       m_low = ta_uf_m_low,
                                       m_high = ta_uf_m_high)
        
        dni_uf = get_simple_util_factor(x = dni, thld = dni_thld, 
                                        m_low = dni_uf_m_low,
                                        m_high = dni_uf_m_high)
        
        uf = (np.multiply(am_uf, am_weight) + np.multiply(ta_uf, ta_weight) 
            + np.multiply(dni_uf, dni_weight))
        
        return uf

    def localize(self, location=None, latitude=None, longitude=None,
                 **kwargs):
        """
        Creates a LocalizedCPVSystem object using this object
        and location data. Must supply either location object or
        latitude, longitude, and any location kwargs

        Parameters
        ----------
        location : None or Location, default None
        latitude : None or float, default None
        longitude : None or float, default None
        **kwargs : see Location

        Returns
        -------
        localized_system : LocalizedCPVSystem
        """

        if location is None:
            location = Location(latitude, longitude, **kwargs)

        return LocalizedCPVSystem(cpvsystem=self, location=location)


class LocalizedCPVSystem(CPVSystem, Location):
    """
    The LocalizedCPVSystem class defines a standard set of installed CPV
    system attributes and modeling functions. This class combines the
    attributes and methods of the CPVSystem and Location classes.

    The LocalizedCPVSystem may have bugs due to the difficulty of
    robustly implementing multiple inheritance. See
    :py:class:`~pvlib.modelchain.ModelChain` for an alternative paradigm
    for modeling PV systems at specific locations.
    """
    def __init__(self, cpvsystem=None, location=None, **kwargs):

        # get and combine attributes from the cpvsystem and/or location
        # with the rest of the kwargs

        if cpvsystem is not None:
            cpv_dict = cpvsystem.__dict__
        else:
            cpv_dict = {}

        if location is not None:
            loc_dict = location.__dict__
        else:
            loc_dict = {}

        new_kwargs = dict(list(cpv_dict.items()) +
                          list(loc_dict.items()) +
                          list(kwargs.items()))

        CPVSystem.__init__(self, **new_kwargs)
        Location.__init__(self, **new_kwargs)

    def __repr__(self):
        attrs = ['name', 'latitude', 'longitude', 'altitude', 'tz', 'module', 
                 'inverter', 'albedo', 'racking_model']
        return ('LocalizedCPVSystem: \n  ' + '\n  '.join(
            ('{}: {}'.format(attr, getattr(self, attr)) for attr in attrs)))


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
        
        CPVSystem.__init__(self,
                     module, module_parameters, modules_per_string,
                     strings_per_inverter, inverter, inverter_parameters,
                     racking_model, losses_parameters, name, **kwargs)
	
    def __repr__(self):
        attrs = ['name', 'module', 'inverter', 'racking_model']
        return ('StaticCPVSystem: \n  ' + '\n  '.join(
            ('{}: {}'.format(attr, getattr(self, attr)) for attr in attrs)))
    
    def get_aoi(self, solar_zenith, solar_azimuth):
        """
        Get the angle of incidence on the Static CPV System.

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

        aoi = irradiance.aoi(self.surface_tilt, self.surface_azimuth,
                             solar_zenith, solar_azimuth)
        return aoi

    def get_irradiance(self, solar_zenith, solar_azimuth, dni, ghi, dhi,
                       dni_extra=None, airmass=None, model='haydavies',
                       **kwargs):
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

        return irradiance.get_total_irradiance(self.surface_tilt,
                                               self.surface_azimuth,
                                               solar_zenith, solar_azimuth,
                                               dni, ghi, dhi,
                                               dni_extra=dni_extra,
                                               airmass=airmass,
                                               model=model,
                                               albedo=self.albedo,
                                               **kwargs)

    def get_aoi_util_factor(self, aoi, aoi_thld, aoi_uf_m_low, aoi_uf_m_high):
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
                
        aoi_uf = get_simple_util_factor(x = aoi, thld = aoi_thld, 
                                        m_low = aoi_uf_m_low,
                                        m_high = aoi_uf_m_high)
        
        if aoi_uf < 0:
            return 0
        
        return aoi_uf
    
    def localize(self, location=None, latitude=None, longitude=None,
                 **kwargs):
        """
        Creates a LocalizedStaticCPVSystem object using this object
        and location data. Must supply either location object or
        latitude, longitude, and any location kwargs

        Parameters
        ----------
        location : None or Location, default None
        latitude : None or float, default None
        longitude : None or float, default None
        **kwargs : see Location

        Returns
        -------
        localized_system : LocalizedStaticCPVSystem
        """

        if location is None:
            location = Location(latitude, longitude, **kwargs)

        return LocalizedStaticCPVSystem(staticcpvsystem=self, 
                                        location=location)


class LocalizedStaticCPVSystem(CPVSystem, Location):
    """
    The LocalizedStaticCPVSystem class defines a standard set of installed 
    Static CPV system attributes and modeling functions. This class combines 
    the attributes and methods of the StaticCPVSystem and Location classes.

    The LocalizedStaticCPVSystem may have bugs due to the difficulty of
    robustly implementing multiple inheritance. See
    :py:class:`~pvlib.modelchain.ModelChain` for an alternative paradigm
    for modeling PV systems at specific locations.
    """
    def __init__(self, staticcpvsystem=None, location=None, **kwargs):

        # get and combine attributes from the staticcpvsystem and/or location
        # with the rest of the kwargs

        if staticcpvsystem is not None:
            staticcpv_dict = staticcpvsystem.__dict__
        else:
            staticcpv_dict = {}

        if location is not None:
            loc_dict = location.__dict__
        else:
            loc_dict = {}

        new_kwargs = dict(list(staticcpv_dict.items()) +
                          list(loc_dict.items()) +
                          list(kwargs.items()))

        StaticCPVSystem.__init__(self, **new_kwargs)
        Location.__init__(self, **new_kwargs)

    def __repr__(self):
        attrs = ['name', 'latitude', 'longitude', 'altitude', 'tz',
                 'surface_tilt', 'surface_azimuth', 'module', 'inverter',
                 'albedo', 'racking_model']
        return ('LocalizedStaticCPVSystem: \n  ' + '\n  '.join(
            ('{}: {}'.format(attr, getattr(self, attr)) for attr in attrs)))



def get_simple_util_factor(x, thld, m_low, m_high):
    """
    Retrieves the utilization factor for a variable.
    
    Parameters
    ----------
    x : numeric / array-like
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
    if not isinstance(x, np.ndarray):
        x = np.array(x, ndmin=1)
    
    suf = []
    
    for i in range(len(x)):
        if x[i] <= thld:
            simple_uf = 1 + (x[i] - thld) * m_low
        else:
            simple_uf = 1 + (x[i] - thld) * m_high
        
        suf.append(simple_uf)
    
    return suf


def calc_uf_lines(x, y, datatype = 'airmass', limit = None):
    """
    Calculates the parameters of two regression lines for a utilization factor
    specified by datatype.
    
    Parameters
    ----------
    x : list or numpy.array of float
    
    y : list or numpy.array of float
    
    datatype : string
        indicates the type of parameter contained in x.
    
    limit : numeric, optional
        forces the limit between the regression lines.
    
    Returns
    -------
    m_low : numeric
        inclination of the first regression line of the utilization factor.
    
    n_low : numeric
        ordinate at the origin of the first regression line.
    
    m_high : numeric
        inclination of the second regression line of the utilization factor.
    
    n_high : numeric
        ordinate at the origin of the second regression line.
    
    thld : numeric
        limit between the two regression lines of the utilization factor.
    """
    
    if datatype == 'airmass' or datatype == 'aoi':
        return calc_two_regression_lines(x, y, limit)
    
    elif datatype == 'temp_air':
        m_low, n_low, rmsd_low = calc_regression_line(x, y)
        
        if limit is None:
            limit = 50
        
        n_high = m_low * limit + n_low
        return m_low, n_low, 0, n_high, limit
    
    else:
        return 0, 0, 0, 0, 0


def calc_two_regression_lines(x, y, limit):
    """
    Calculates the parameters of two regression lines for the composed 
    utilization factors.
    
    Parameters
    ----------
    x : list or numpy.array of float
    
    y : list or numpy.array of float
    
    limit : numeric, optional
        forces the limit between the regression lines.
    
    Returns
    -------
    m_low : numeric
        inclination of the first regression line of the utilization factor.
    
    n_low : numeric
        ordinate at the origin of the first regression line.
    
    m_high : numeric
        inclination of the second regression line of the utilization factor.
    
    n_high : numeric
        ordinate at the origin of the second regression line.
    
    thld : numeric
        limit between the two regression lines of the utilization factor.
    """
    
    if limit is None:
        m_low, n_low, m_high, n_high, thld = 0, 0, 0, 0, 0
        rmsd = 10000
        
        # The x array is traversed in order to find the most fitting 
        # regression lines.
        for i in np.arange(x[0], x[-2], 0.1):
            # Auxiliar variables initialization.
            x_aux1 = []
            x_aux2 = []
    
            y_aux1 = [] 
            y_aux2 = [] 
            
            # The original measurements are divided into two sets by the limit.
            for j in range(len(x)):
                if x[j] <= i:
                    x_aux1.append(x[j])
                    y_aux1.append(y[j])
                else:
                    x_aux2.append(x[j])
                    y_aux2.append(y[j])
                
            # Regression lines are calculated for the two sets.
            m_low_temp, n_low_temp, rmsd_low_temp = calc_regression_line(
                    x_aux1, y_aux1)
            
            m_high_temp, n_high_temp, rmsd_high_temp = calc_regression_line(
                    x_aux2, y_aux2)
        
            # Less suitable regression lines are rejected.
            rmsd_temp = rmsd_low_temp + rmsd_high_temp
        
            if rmsd_temp < rmsd:
                m_low = m_low_temp
                n_low = n_low_temp
                m_high = m_high_temp
                n_high = n_high_temp
                rmsd = rmsd_temp
    
        # The intersection between the two final regression lines is calculated.
        thld = (n_high - n_low) / (m_low - m_high)
    
    else:
        # Auxiliar variables initialization.
        x_aux1 = []
        x_aux2 = []
    
        y_aux1 = [] 
        y_aux2 = [] 
    
        # The original measurements are divided into two sets by the limit.
        for j in range(len(x)):
            if x[j] <= limit:
                x_aux1.append(x[j])
                y_aux1.append(y[j])
            else:
                x_aux2.append(x[j])
                y_aux2.append(y[j])
        
        # Regression lines are calculated for the two sets.
        m_low, n_low, rmsd_low = calc_regression_line(x_aux1, y_aux1)
            
        m_high, n_high, rmsd_high = calc_regression_line(x_aux2, y_aux2)
        
        # The intersection between the two final regression lines is 
        # calculated as it can not be exactly the limit forced.
        thld = (n_high - n_low) / (m_low - m_high)
    
    return m_low, n_low, m_high, n_high, thld


def calc_regression_line(x, y):
    """
    Wrapper for regression line calcs.
        
    Parameters
    ----------
    x : array of numbers
    
    y : array of numbers
    
    Returns
    -------
    m : numeric
        inclination of the regression line.
        
    n : numeric
        ordinate at the origin of the regression line.
        
    rmsd : numeric
        root-mean-square deviation between the regression line and the 
        measurements.
    """
    
    # Initial input treatment.
    if not isinstance(x, np.ndarray):
        x = np.array(x)
    x = x[:, np.newaxis]
    
    if not isinstance(y, np.ndarray):
        y = np.array(y)
    y = y[:, np.newaxis]
    
    # The regression line model is executed.
    model = linear_model.LinearRegression()
    model.fit(x, y)
    
    # Coeficients of the line are obtained.
    m = model.coef_[0][0]
    
    n = model.intercept_[0]
    
    # The root-mean-square deviation is calculated.
    y_pred = model.predict(x)
    
    rmsd = math.sqrt(mean_squared_error(y, y_pred))
    
    return m, n, rmsd




































