import logging
from pathlib import Path
import fnmatch


import numpy as np
import xarray as xr
from xarray.backends import BackendEntrypoint

import epygram
epygram.init_env()

import faengine.backend.readers as readers
import faengine.backend.formatters as formatters
from faengine.settings import defaultsettings




class FAEngine(BackendEntrypoint):
    
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
    custom_settings={},

    ):
        # Update defualt settings
        settings = defaultsettings
        settings.update(custom_settings)



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
            fieldnames = [f for f in fieldnames if f not in drop_variables]

        d2fields = r.readfields(fieldnames)
       

        #Dummy field --> used for geometry and validity extraction
        dummy_field = d2fields[0] #first of targets


        # ---  Create dims ----- 
        #Note: These are dataset dims, not all fields needs all these dims
            # Name the dimensions
        dim_order = [settings['coordnames']['validtime'],
                     settings['coordnames']['zdim'],
                     settings['coordnames']['ydim'],
                    settings['coordnames']['xdim']]
        
        if create_base_dimension:
            dim_order.insert(0, settings['coordnames']['basetime'])
        

        # --- Create (data) variables --- 
        dataset_variables = {}
        for field in d2fields:
            if field.spectral:
                field.sp2gp()

            #TODO extract subdomain

            #get fieldname
            fieldname = field.fid['FA']

            #Add trivial time dimension
            fieldata = np.array([field.data]) #add trivial time dimension

            # Name the dimensions of the field (ORDER IS IMPORTANT)
            fielddim_order = [
                settings['coordnames']['validtime'],
                settings['coordnames']['ydim'],
                settings['coordnames']['xdim']] #TODO this is for 2D only!! 

            # Add extra reference time dimension (Cycling experiments)
            if create_base_dimension:
                fieldata =  np.array([fieldata])
                fielddim_order.insert(0, settings['coordnames']['basetime'])

            field_attrs = formatters.fmt_dict_for_attrs(field.fid)
        
            #to xarray
            dataset_variables[fieldname] = xr.Variable(
                    dims=fielddim_order, 
                    data=fieldata,
                    attrs=field_attrs,
                    )
        
        # --- Create coordinates --- 
    
        validtime =readers.read_validdate(epyfield=dummy_field)
        dataset_coords = {
            #Dims-coords
            settings['coordnames']['xdim']: readers.read_x_dim(dummy_field),
            settings['coordnames']['ydim']: readers.read_y_dim(dummy_field),
            settings['coordnames']['validtime']: formatters.fmt_validtime_variable(
                validtime=validtime,
                dimname=settings['coordnames']['validtime']),
        }
        if create_base_dimension:
            referencetime = readers.read_basedate(epyfield=dummy_field)
            dataset_coords[settings['coordnames']['basetime']] = formatters.fmt_basedate_variable(
                basedate=referencetime,
                dimname=settings['coordnames']['basetime'])

        if add_latlon_coords:
            lats, lons = readers.read_lat_lons(epyfield=dummy_field)
            #Dependent coords
            dataset_coords[settings['coordnames']['latcoord']]= formatters.fmt_lat_variable(lats)
            dataset_coords[settings['coordnames']['loncoord']]= formatters.fmt_lon_variable(lons)



        # --- Reading attributes ----
        dataset_attrs={}

        #1. Read the CRS 
        crs = readers.read_proj(epyfield=dummy_field) #read
        dataset_attrs['proj_crs'] = formatters.fmt_proj(crs) # format

        #2. Time details
        validtime = readers.read_validdate(epyfield=dummy_field)
        dataset_attrs['validtime'] = formatters.fmt_timestamp(validtime)

        basedate = readers.read_basedate(epyfield=dummy_field)
        dataset_attrs['basedate'] = formatters.fmt_timestamp(basedate)

        cumul_delta = readers.read_cumulativeduration(epyfield=dummy_field)
        dataset_attrs['cumuldelta'] = formatters.fmt_timedelta(cumul_delta)

        #3. Vertical details
        vertical_details = readers.read_vertical_attrs(r),
        dataset_attrs.update(formatters.fmt_dict_for_attrs(vertical_details))
    
        #Construct the dataset
        ds = xr.Dataset(data_vars= {**dataset_variables},
                        coords={**dataset_coords},
                        attrs=dataset_attrs)
        
        #Close the readers
        r.close() #this becomes problematic when lazy-loading i think.
        

        
        return ds





