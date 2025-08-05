""" Collection of functions to extract data from Epygram objects. """


import logging
import pandas as pd
import numpy as np


# ------------------------------------------
#    Dimensions
# ------------------------------------------

def read_x_dim(epyfield) -> np.array:
    xvals = epyfield.geometry._get_grid(indextype='xy')[0][0,:]
    return np.array(xvals)

def read_y_dim(epyfield) -> np.array:
    yvals = epyfield.geometry._get_grid(indextype='xy')[1][:,0]
    return np.array(yvals)

# ------------------------------------------
#    proj related
# ------------------------------------------

def read_proj(epyfield):
    crs = epyfield.geometry.default_cartopy_CRS()
    return crs


def read_grid_details(epyfield) -> dict:
    return epyfield.geometry.dimensions

def read_lat_lons(epyfield):
    lons, lats = epyfield.geometry.get_lonlat_grid()
    return lons, lats


# ------------------------------------------
#    time related
# ------------------------------------------

def read_basedate(epyfield) -> str:
    return epyfield.validity.getbasis().isoformat()


def read_validdate(epyfield) -> str:
    return epyfield.validity.get().isoformat()

def read_cumulativeduration(epyfield) -> str:
    return str(epyfield.validity.cumulativeduration())


# ------------------------------------------
#    vertical coordinates
# ------------------------------------------

def read_vertical_attrs(epyresource) -> dict:
    vcoords = epyresource.geometry.vcoordinate
    return vcoords.grid




# ------------------------------------------
#    general attributes
# ------------------------------------------

def read_h2d_field_attrs(epyfield) -> dict:
    attrs = epyfield.fid
    #'generic' is a nested dict, unnest it 
    if 'generic' in attrs.keys():
        if isinstance(attrs['generic'], dict):
            attrs.update(attrs['generic'])
            attrs.pop('generic')

    return attrs