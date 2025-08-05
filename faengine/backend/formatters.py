""" Collection of formatters to put data in a xarray-complient format"""

import pandas as pd
import numpy as np
from xarray import Variable


def fmt_proj(projcrs) -> str:
    """
    Format a projection CRS object to WKT string.

    Parameters
    ----------
    projcrs : cartopy.crs.CRS
        The projection CRS object.

    Returns
    -------
    str
        WKT representation of the CRS.
    """
    return str(projcrs.to_wkt())


def fmt_timestamp_to_str(timestamp: str) -> str:
    """
    Convert a timestamp string to ISO datetime64 string.

    Parameters
    ----------
    timestamp : str
        Timestamp string.

    Returns
    -------
    str
        ISO formatted datetime64 string.
    """
    return str(np.datetime64(pd.to_datetime(timestamp)))


def fmt_timedelta_to_str(timedelta: str) -> str:
    """
    Convert a timedelta string to ISO format.

    Parameters
    ----------
    timedelta : str
        Timedelta string.

    Returns
    -------
    str
        ISO formatted timedelta string or 'None'.
    """
    if (timedelta == 'None') or timedelta is None:
        return 'None'
    
    return str(pd.to_timedelta(timedelta).isoformat())

def fmt_variablename(name: str) -> str:
    """
    Format a variable name for xarray compatibility.

    Parameters
    ----------
    name : str
        Variable name.

    Returns
    -------
    str
        Formatted variable name.
    """
    # i think underscar or point are not allowd?
    return name

def fmt_dict_for_attrs(attrs: dict) -> tuple:
    """
    Format a dictionary for use as xarray attributes.

    Parameters
    ----------
    attrs : dict
        Attributes dictionary.

    Returns
    -------
    tuple
        Tuple of attribute key-value pairs.
    """
    #TODO (replace undescar?)
    
    if isinstance(attrs, dict):
        new_attrs = {}
        for k, v in attrs.items():
            if isinstance(v, dict):
                # Recursively convert nested dict to tuple
                new_attrs[k] = tuple(v.items())
            elif isinstance(v, (int, float, str, list, tuple)):
                new_attrs[k] = v
            else:
                raise TypeError(f"Value for key '{k}' is not a supported type: {type(v)}")
        attrs = new_attrs
        return tuple(attrs.items())

    elif isinstance(attrs, tuple):
        return attrs
    else:
        raise TypeError(f'attrs is not a dict or tuple (but a {type(attrs)})')
        
    

# ------------------------------------------
#    Formatters for xarray objects
# ------------------------------------------

def fmt_lat_variable(latarray) -> Variable:
    """
    Format a latitude array as an xarray Variable.

    Parameters
    ----------
    latarray : np.ndarray
        Latitude array.

    Returns
    -------
    xarray.Variable
        xarray Variable for latitude.
    """
    #CF conv
    attrs = {
        'long_name': 'latitude',
        'units': 'degrees_north'
    }
    #extra attributes
    attrs['fill_value'] = latarray.fill_value

    return Variable(dims=['y', 'x'],
                    data=latarray,
                    attrs=fmt_dict_for_attrs(attrs))

def fmt_lon_variable(lonarray) -> Variable:
    """
    Format a longitude array as an xarray Variable.

    Parameters
    ----------
    lonarray : np.ndarray
        Longitude array.

    Returns
    -------
    xarray.Variable
        xarray Variable for longitude.
    """
    #CF conv
    attrs = {
        'long_name': 'longitude',
        'units': 'degrees_east'
    }
    #extra attributes
    attrs['fill_value'] = lonarray.fill_value

    return Variable(dims=['y', 'x'],
                    data=lonarray,
                    attrs=fmt_dict_for_attrs(attrs))


def fmt_validtime_variable(validtime, dimname: str) -> Variable:
    """
    Format a valid time as an xarray Variable.

    Parameters
    ----------
    validtime : str or array-like
        Valid time(s).
    dimname : str
        Name of the time dimension.

    Returns
    -------
    xarray.Variable
        xarray Variable for valid time.
    """
    # CF-compliant attributes
    attrs = {
        "standard_name": "time",
        "long_name": "time",
        # "units": "seconds since 1970-01-01T00:00:00Z",
        # "calendar": "gregorian"
    }
    return create_1D_time_variable(datetime=validtime, 
                                   dimname=dimname,
                                   var_attrs=attrs)


def fmt_basedate_variable(basedate: pd.Timestamp, dimname: str) -> Variable:
    """
    Format a base date as an xarray Variable.

    Parameters
    ----------
    basedate : pd.Timestamp
        Base date timestamp.
    dimname : str
        Name of the time dimension.

    Returns
    -------
    xarray.Variable
        xarray Variable for base date.
    """
    # CF-compliant attributes
    attrs = {
        "standard_name": "reference_time",
        "long_name": "time of the start of forecast",
        # "units": "seconds since 1970-01-01T00:00:00Z",
        # "calendar": "gregorian"
    }
    return create_1D_time_variable(datetime=basedate, 
                                   dimname=dimname,
                                   var_attrs=attrs)
   

# ------------------------------------------
#    Helpers
# ------------------------------------------

def create_1D_time_variable(datetime, dimname: str, var_attrs: dict) -> Variable:
    """
    Create a 1D xarray Variable for time data.

    Parameters
    ----------
    datetime : str, pd.Timestamp, np.datetime64, or iterable
        Time value(s).
    dimname : str
        Name of the time dimension.
    var_attrs : dict
        Attributes for the variable.

    Returns
    -------
    xarray.Variable
        1D time variable.
    """
    # Accept single or multiple timestamps
    if isinstance(datetime, (pd.Timestamp, np.datetime64, str)):
        data = np.array([np.datetime64(datetime)])
    else:
        # Assume iterable
        data = np.array([np.datetime64(v) for v in datetime])
    
    return Variable(dims=[dimname], data=data, attrs=var_attrs)