""" Collection of functions to extract data from Epygram objects. """


import logging
import pandas as pd
import numpy as np


# ------------------------------------------
#    Dimensions
# ------------------------------------------

def read_x_dim(epyfield) -> np.ndarray:
    """
    Extract the x-dimension values from an Epygram field.

    Parameters
    ----------
    epyfield : Epygram field
        The Epygram field object.

    Returns
    -------
    np.ndarray
        Array of x-dimension values.
    """
    xvals = epyfield.geometry._get_grid(indextype='xy')[0][0,:]
    return np.array(xvals)

def read_y_dim(epyfield) -> np.ndarray:
    """
    Extract the y-dimension values from an Epygram field.

    Parameters
    ----------
    epyfield : Epygram field
        The Epygram field object.

    Returns
    -------
    np.ndarray
        Array of y-dimension values.
    """
    yvals = epyfield.geometry._get_grid(indextype='xy')[1][:,0]
    return np.array(yvals)

# ------------------------------------------
#    proj related
# ------------------------------------------

def read_proj(epyfield) -> 'Cartopy.crs.CRS':
    """
    Get the cartopy CRS from the Epygram field geometry.

    Parameters
    ----------
    epyfield : Epygram field
        The Epygram field object.

    Returns
    -------
    cartopy.crs.CRS
        The cartopy coordinate reference system.
    """
    crs = epyfield.geometry.default_cartopy_CRS()
    return crs


def read_grid_details(epyfield) -> dict:
    """
    Get grid dimension details from the Epygram field geometry.

    Parameters
    ----------
    epyfield : Epygram field
        The Epygram field object.

    Returns
    -------
    dict
        Dictionary of grid dimensions.
    """
    return epyfield.geometry.dimensions

def read_lat_lons(epyfield):
    """
    Get longitude and latitude grids from the Epygram field geometry.

    Parameters
    ----------
    epyfield : Epygram field
        The Epygram field object.

    Returns
    -------
    tuple of np.ndarray
        Tuple containing (lons, lats) arrays.
    """
    lons, lats = epyfield.geometry.get_lonlat_grid()
    return lons, lats


# ------------------------------------------
#    time related
# ------------------------------------------

def read_basedate(epyfield) -> str:
    """
    Get the base date (reference time) of the field validity.

    Parameters
    ----------
    epyfield : Epygram field
        The Epygram field object.

    Returns
    -------
    str
        ISO formatted base date string.
    """
    basedate = epyfield.validity.getbasis() #Get datetime.datetime
    basedate = _check_timestamp(basedate) #format to pd.timestamp and check for pgd
    return basedate.isoformat() #to str


def read_validdate(epyfield) -> str:
    """
    Get the valid date (forecast time) of the field.

    Parameters
    ----------
    epyfield : Epygram field
        The Epygram field object.

    Returns
    -------
    str
        ISO formatted valid date string.
    """
    validate = epyfield.validity.get() #get validate as dattime.datetime
    validate = _check_timestamp(validate) #to pd.timestamp and pgd checking
    return validate.isoformat() #to string

def read_cumulativeduration(epyfield) -> str:
    """
    Get the cumulative duration of the field validity.

    Parameters
    ----------
    epyfield : Epygram field
        The Epygram field object.

    Returns
    -------
    str
        String representation of the cumulative duration.
    """
    return str(epyfield.validity.cumulativeduration())


# ------------------------------------------
#    vertical coordinates
# ------------------------------------------

def read_vertical_attrs(epyresource) -> dict:
    """
    Get vertical coordinate attributes from the Epygram resource.

    Parameters
    ----------
    epyresource : Epygram resource
        The Epygram resource object.

    Returns
    -------
    dict
        Dictionary of vertical coordinate grid attributes.
    """
    vcoords = epyresource.geometry.vcoordinate
    return vcoords.grid




# ------------------------------------------
#    general attributes
# ------------------------------------------

def read_h2d_field_attrs(epyfield) -> dict:
    """
    Extract and flatten the attributes dictionary from an Epygram field.

    Parameters
    ----------
    epyfield : Epygram field
        The Epygram field object.

    Returns
    -------
    dict
        Dictionary of field attributes.
    """
    attrs = epyfield.fid
    # 'generic' is a nested dict, unnest it 
    if 'generic' in attrs.keys():
        if isinstance(attrs['generic'], dict):
            attrs.update(attrs['generic'])
            attrs.pop('generic')

    return attrs


# ------------------------------------------
#    helpers
# ------------------------------------------

def _check_timestamp(timestamp) -> pd.Timestamp:
    timestamp = pd.Timestamp(timestamp)
    if timestamp.year == 1:
        #This is indication of PGD file !! set validtime an reference timme 
        #to unix epoch 
        timestamp = pd.Timestamp(0)

    return timestamp
   