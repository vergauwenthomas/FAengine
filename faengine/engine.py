import logging
from pathlib import Path
import fnmatch
import re

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
        H2D_fieldnameset, ATM3D_fieldnameset = triage_2d_and_3d_fields(fieldnames=fieldnames) 
        
        dummy_field = None
        dataset_variables = {}
        # ---- 2D Fields ----

        for fieldname, _ in H2D_fieldnameset.items():
            
            #Read the field
            try: 
                field = r.readfield(fieldname)
            except Exception as e:
                print(f"An error occurred reading {fieldname}: {e}")
            
            else:
                if isinstance(field, epygram.fields.H2DField):
                    fmt_fieldname = formatters.fmt_variablename(field.fid['FA'])
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
        
        # --- 3D Fields ---- 
        for basename in ATM3D_fieldnameset.keys():
            fmt_fieldname = formatters.fmt_variablename(basename)
            target_H2D_colletion = ATM3D_fieldnameset[basename]

            rcl = epygram.resources.meta_resource(
                filenames_or_resources=r,
                openmode='r',
                rtype= 'CL')
            
            #create 3d variable
            epy_3d = construct_epy_3D(targetfieldnames=target_H2D_colletion,
                                      epyresource=r,
                                      epyCLresource=rcl)
            if dummy_field is None:
                    dummy_field = epy_3d
            #to xarray variable
            dataset_variables[fmt_fieldname] = epy_3D_to_vriable(field=epy_3d,
                                                                 fieldname=basename,
                                                                 create_base_dim=create_base_dimension,
                                                                 namesettings=namesettings,
                                                                 unitsettings=unitsettings)
            #close CL resource
            rcl.close()





        # --- Create coordinates --- 
    
        validtime =readers.read_validdate(epyfield=dummy_field)
        dataset_coords = {
            #Dims-coords
            namesettings['coordnames']['zdim']: readers.read_z_dim(r),
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
        vertical_details = readers.read_vertical_attrs(r)
        dataset_attrs.update(formatters.fmt_dict_for_attrs(vertical_details))
    
        #Construct the dataset
        ds = xr.Dataset(data_vars= {**dataset_variables},
                        coords={**dataset_coords},
                        attrs=dataset_attrs)
        
        #Close the readers
        r.close() #this becomes problematic when lazy-loading i think.

        ds = reduce_artificial_dimensions(ds=ds, namesettings=namesettings)
        
        return ds


def reduce_artificial_dimensions(ds, namesettings):
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

    
    #Test if vertical info is present --> PGD file or not

    #a z-dim is always added, so now check if it is artificial
    if ds['z'].shape == (1,):
        #drop the vertical dimension
        ds.attrs['zdim_detected'] = 'False'
        ds = ds.isel({namesettings['coordnames']['zdim']: 0})
    else:
        ds.attrs['zdim_detected'] = 'True'
        
    return ds
        
def triage_2d_and_3d_fields(fieldnames, d3rex="^S[0-9][0-9][0-9].*"):
    """
    Categorizes field names into 2D and 3D fields based on a given regex pattern.
    Args:
        fieldnames (list of str): List of field names to be categorized.
        d3rex (str, optional): Regular expression pattern to identify 3D fields. 
                               Defaults to "^S[0-9][0-9][0-9].*".
    Returns:
        tuple: A tuple containing two dictionaries:
            - d2_fields (dict): Dictionary of 2D fields where key and value are the field names.
            - d3_fields (dict): Dictionary of 3D fields where key is the base field name and 
                                value is a sorted list of field names matching the base name.
    """
    
    d2_fields = {} #name : fieldname (name = fieldname for 2d)
    d3_fields = {} 
    d3regex = re.compile(d3rex)

    unassigned_fields = fieldnames.copy()
    for field in unassigned_fields: 
        if bool(d3regex.match(field)):
            basefieldname=field[4:]
            specific_rex = re.compile(f'{d3rex}{basefieldname}') #regex to match all fields with the same base name end
            #field is member of 3d fields
            newlist = list(filter(specific_rex.match, unassigned_fields)) # Read Note below
            d3_fields[basefieldname] = newlist 
        else:
            d2_fields[field] = field

    #Sort the d3 fields
    for basename, fields  in d3_fields.items():
        d3_fields[basename] = sorted(fields, key=lambda x: int(x[1:4]))

 
    return d2_fields, d3_fields


def construct_epy_3D(targetfieldnames:list,
                       epyresource,
                       epyCLresource,
                       ):
    

    #One of the issues is that when constructing a combined-level resource,
    #the standard names of fields are not used, but a more complex fid (with different
    #surface defenitions etc) is used. So we need to convert a fieldname to a 3D field,
    # that then can be used for subsetting.

    #Get a dummy H2D field that is a crossection of the 3D field:
    dummy_crossec_fieldname = targetfieldnames[0]

    #get the fid of that variable
    target_fid_dict = epyresource.readfield(dummy_crossec_fieldname).fid['generic']

    #Construct a FID for selecing the 3D field

    #Drop items that are only linked to this crossection
    # to_drop_keys = [
    #     'level', #obvious
    #     'scaleFactorOfFirstFixedSurface', #else keyerror is raised,
    #     'typeOfFirstFixedSurface', #else keyerror is raised,
    #     'typeOfSecondFixedSurface',#else keyerror is raised,
    #     'scaledValueOfFirstFixedSurface',#else keyerror is raised
    #     ]
    # for dropkey in to_drop_keys:
    #     if dropkey in target_fid_dict.keys():
    #         del target_fid_dict[dropkey]

    #Or alternative, select a minimum required parameters (better coding style!)
    target_keys = [
        'parameterCategory',
        'parameterNumber',
        'discipline',
        'tablesVersion',
        'productDefinitionTemplateNumber']

    target_fid_dict = {key:val for key, val in target_fid_dict.items() if key in target_keys}

    #check if a candidate is found in the CL resource
    candidates = epyCLresource.find_fields_in_resource_by_generic_fid(target_fid_dict)

    #Check if there is a candidate
    if len(candidates) == 0:
        raise ValueError(f'None candidate found for FID: {target_fid_dict} in CL resource.')

    #Check if there is only 1 candidate found
    if len(candidates) >1:
        raise ValueError(f'More than one candidate found for FID: {target_fid_dict} in CL resource.')

    #read the field
    d3target_fid_dict = candidates[0]['CombineLevels']
    d3field = epyCLresource.readfield(d3target_fid_dict)

    return d3field


def epy_3D_to_vriable(field, fieldname, create_base_dim:bool, namesettings:dict,
                         unitsettings:dict):
    if field.spectral:
            field.sp2gp()


    #TODO extract subdomain

    #Add trivial time dimension
    fieldata = np.array([field.data]) #add trivial time dimension

    # Name the dimensions of the field (ORDER IS IMPORTANT)
    fielddim_order = [
        namesettings['coordnames']['validtime'],
        namesettings['coordnames']['zdim'],
        namesettings['coordnames']['ydim'],
        namesettings['coordnames']['xdim']]
    
    # Add extra reference time dimension (Cycling experiments)
    if create_base_dim:
        fieldata =  np.array([fieldata])
        fielddim_order.insert(0, namesettings['coordnames']['basetime'])


    # --- Create attributes ---
    #FID attributes
    field_attrs = readers.read_3d_field_attrs(field) 
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
        namesettings['coordnames']['xdim']] 
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

