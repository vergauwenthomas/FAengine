""" Collection of formatters to put data in a xarray-complient format"""

import pandas as pd
import numpy as np
from xarray import Variable


def fmt_proj(projcrs):
    return projcrs.to_wkt()


def fmt_timestamp_to_str(timestamp:str) -> str: 
    return str(np.datetime64(pd.to_datetime(timestamp)))


def fmt_timedelta_to_str(timedelta: str) -> str:
    if (timedelta == 'None') or timedelta is None:
        return 'None'
    
    return str(pd.to_timedelta(timedelta).isoformat())

def fmt_variablename(str):
    #i think underscar or point are not allowd?
    return str

def fmt_dict_for_attrs(attrs:dict): #TODO update typecasting (to union)

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

def fmt_lat_variable(latarray): 
    return Variable(dims=['y', 'x'],
                    data=latarray,
                    attrs={'fill_value': latarray.fill_value})

def fmt_lon_variable(lonarray):
    return fmt_lat_variable(lonarray)


def fmt_validtime_variable(validtime, dimname: str):
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


def fmt_basedate_variable(basedate:pd.Timestamp, dimname:str):

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

def create_1D_time_variable(datetime, dimname:str, var_attrs:dict):
    # Accept single or multiple timestamps
    if isinstance(datetime, (pd.Timestamp, np.datetime64, str)):
        data = np.array([np.datetime64(datetime)])
    else:
        # Assume iterable
        data = np.array([np.datetime64(v) for v in datetime])
    
    return Variable(dims=[dimname], data=data, attrs=var_attrs)