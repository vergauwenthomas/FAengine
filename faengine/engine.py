import logging
from pathlib import Path
import fnmatch

import pandas as pd
import numpy as np
import xarray as xr
from xarray.backends import BackendEntrypoint

import epygram
epygram.init_env()

import faengine.backend.readers as readers
import faengine.backend.formatters as formatters
from faengine.settings import defaultsettings, default_units, default_blackfields




class FAEngine(BackendEntrypoint):
    """
    Xarray backend engine for reading FA files using Epygram.

    This engine enables seamless integration of FA files with xarray by providing
    methods to open and parse FA resources, extract fields, coordinates, and metadata,
    and format them into xarray-compatible datasets.

    """
    
    # open_dataset_parameters = ["filename_or_obj", "drop_variables"]
    description =  "Use FA files in Xarray."
    version = "0.0.1a" #or sync with package?


    def open_dataset(
    self,
    filename_or_obj,
    drop_variables=None, #TODO functionallity

    #--- custom arguments ----
    whitefield_glob=r'*', #glob of fields
    blackfield_glob='', #glob expression 
    add_latlon_coords= True,
    create_base_dimension = True,
    # drop_extension_zone = True,
    # construct_3d_fields=True,
    custom_name_settings={},
    custom_unit_settings={},

    ):
        # Update defualt settings
        namesettings = defaultsettings
        namesettings.update(custom_name_settings)

        unitsettings = default_units
        unitsettings.update(custom_unit_settings)

        #1 ---- Read the resource
        r = epygram.open(
                filename=str(filename_or_obj),
                openmode='r',
                fmt='FA',
                fmtdelayedopen=True)
    
        
        # 2.--- Subset to target fields ----
        fieldnames = r.find_fields_in_resource(whitefield_glob)
        if not bool(fieldnames):
            raise ValueError(f'No fields found for {whitefield_glob}! Here are all the fields: {r.listfields()}.')

        # apply black-regex filter
        if blackfield_glob:
            fieldnames = [f for f in fieldnames if not fnmatch.fnmatch(f, blackfield_glob)]

        # --- Apply drop_variables functionality ---
        if drop_variables is not None:
            if isinstance(drop_variables, str):
                drop_variables = [drop_variables]
            fieldnames = list(set(fieldnames)- set(drop_variables))
        
        #apply default blacklist
        fieldnames = list(set(fieldnames)- set(default_blackfields))

      

        # ---  Create dims ----- 
        #Note: These are dataset dims, not all fields needs all these dims
            # Name the dimensions
        dim_order = [namesettings['coordnames']['validtime'],
                     namesettings['coordnames']['zdim'],
                     namesettings['coordnames']['ydim'],
                     namesettings['coordnames']['xdim']]
        
        if create_base_dimension:
            dim_order.insert(0, namesettings['coordnames']['basetime'])
        

        # --- Create (data) variables --- 
        dataset_variables = {}
        dummy_field = None
        for fieldname in fieldnames:
            #Read the field
            try: 
                field = r.readfield(fieldname)
            except Exception as e:
                print(f"An error occurred reading {fieldname}: {e}")
            
            else:
                if isinstance(field, epygram.fields.H2DField):
                    fieldname = field.fid['FA']
                    fmt_fieldname = formatters.fmt_variablename(fieldname)
                    dataset_variables[fmt_fieldname] = epy_H2D_to_variable(
                        field=field,
                        create_base_dim=create_base_dimension,
                        namesettings=namesettings,
                        unitsettings=unitsettings)
                    if dummy_field is None:
                        dummy_field = field
                else:
                    logging.warning(f"Field '{fieldname}' is not a H2D field and will be skipped.")
                    continue
            
        # --- Create coordinates --- 
    
        validtime =readers.read_validdate(epyfield=dummy_field)
        dataset_coords = {
            #Dims-coords
            namesettings['coordnames']['xdim']: readers.read_x_dim(dummy_field),
            namesettings['coordnames']['ydim']: readers.read_y_dim(dummy_field),
            namesettings['coordnames']['validtime']: formatters.fmt_validtime_variable(
                validtime=validtime,
                dimname=namesettings['coordnames']['validtime']),
        }
        if create_base_dimension:
            referencetime = readers.read_basedate(epyfield=dummy_field)
            dataset_coords[namesettings['coordnames']['basetime']] = formatters.fmt_basedate_variable(
                basedate=referencetime,
                dimname=namesettings['coordnames']['basetime'])

        if add_latlon_coords:
            lats, lons = readers.read_lat_lons(epyfield=dummy_field)
            #Dependent coords
            dataset_coords[namesettings['coordnames']['latcoord']]= formatters.fmt_lat_variable(lats)
            dataset_coords[namesettings['coordnames']['loncoord']]= formatters.fmt_lon_variable(lons)

        # --- Reading attributes ----
        dataset_attrs={}

        #1. Read the CRS 
        crs = readers.read_proj(epyfield=dummy_field) #read
        dataset_attrs['proj_crs'] = formatters.fmt_proj(crs) # format

        #2. Time details
        validtime = readers.read_validdate(epyfield=dummy_field)
        dataset_attrs['validtime'] = formatters.fmt_timestamp_to_str(validtime)

        basedate = readers.read_basedate(epyfield=dummy_field)
        dataset_attrs['basedate'] = formatters.fmt_timestamp_to_str(basedate)

        cumul_delta = readers.read_cumulativeduration(epyfield=dummy_field)
        dataset_attrs['cumuldelta'] = formatters.fmt_timedelta_to_str(cumul_delta)

        #3. Vertical details
        vertical_details = readers.read_vertical_attrs(r),
        dataset_attrs.update(formatters.fmt_dict_for_attrs(vertical_details))
    
        #Construct the dataset
        ds = xr.Dataset(data_vars= {**dataset_variables},
                        coords={**dataset_coords},
                        attrs=dataset_attrs)
        
        #Close the readers
        r.close() #this becomes problematic when lazy-loading i think.

        ds = static_test(ds=ds, namesettings=namesettings)
        
        return ds


def static_test(ds, namesettings):
    #test if the FA file is static --> PGD file
    unix_epoch = pd.Timestamp(0)
    is_pgd = (((pd.Timestamp(ds.attrs['validtime']) - unix_epoch) < pd.Timedelta('1s')) &
        ((ds.attrs['basedate'] == ds.attrs['validtime'])))
    
    if is_pgd:
        ds.attrs['PGD_detected'] = 'True'
        #Drop all the time dimensions 
        ds = (ds
              .isel({namesettings['coordnames']['validtime']:0,
                     namesettings['coordnames']['basetime']: 0})
            )
    else: 
        ds.attrs['PGD_detected'] = 'False'
        
    return ds
        



def epy_H2D_to_variable(field, create_base_dim:bool, namesettings:dict,
                         unitsettings:dict):
    if field.spectral:
            field.sp2gp()

    #TODO extract subdomain

    #get fieldname
    fieldname = field.fid['FA']

    #Add trivial time dimension
    fieldata = np.array([field.data]) #add trivial time dimension

    # Name the dimensions of the field (ORDER IS IMPORTANT)
    fielddim_order = [
        namesettings['coordnames']['validtime'],
        namesettings['coordnames']['ydim'],
        namesettings['coordnames']['xdim']] #TODO this is for 2D only!! 

    # Add extra reference time dimension (Cycling experiments)
    if create_base_dim:
        fieldata =  np.array([fieldata])
        fielddim_order.insert(0, namesettings['coordnames']['basetime'])


    # --- Create attributes ---
    #FID attributes
    field_attrs = readers.read_h2d_field_attrs(field) 
    field_attrs.update(
        {'short_name': fieldname}
    )
    
    #unit attributes
    if fieldname in unitsettings.keys():
        unit = unitsettings[fieldname]
    else:
        unit='Unknown'
    field_attrs['units'] = unit


    
    #to xarray
    var = xr.Variable(
            dims=fielddim_order, 
            data=fieldata,
            attrs=formatters.fmt_dict_for_attrs(field_attrs),
            )
    return var

