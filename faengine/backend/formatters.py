""" Collection of formatters to put data in a xarray-complient format"""

import pandas as pd
import numpy as np
from xarray import Variable


def fmt_proj(projcrs):
    return projcrs.to_wkt()


def fmt_timestamp(timestamp:str): 
    return pd.to_datetime(timestamp)


def fmt_timedelta(timedelta: str):
    if timedelta == 'None':
        return None
    return pd.to_timedelta(timedelta)

def fmt_variablename(str):
    #i think underscar or point are not allowd?
    return str

def fmt_dict_for_attrs(dict):
    #TODO (replace undescar?)
    return dict


# ------------------------------------------
#    Formatters for xarray objects
# ------------------------------------------

def fmt_lat_variable(latarray): 
    return Variable(dims=['y', 'x'],
                    data=latarray,
                    attrs={'fill_value': latarray.fill_value})

def fmt_lon_variable(lonarray):
    return fmt_lat_variable(lonarray)

def fmt_validtime_variable(validtime:pd.Timestamp, dimname:str):
    return Variable(dims=[dimname],
                    data=np.array([fmt_timestamp(validtime)]))

def fmt_basedate_variable(basedate:pd.Timestamp, dimname:str):
    return Variable(dims=[dimname],
                    data=np.array([fmt_timestamp(basedate)]))

