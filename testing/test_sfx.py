import pytest
import sys
from pathlib import Path

# import metobs_toolkit
import pandas as pd
import xarray as xr
import numpy as np


libfolder = Path(str(Path(__file__).resolve())).parent.parent

# point to current version of the faengine
sys.path.insert(1, str(libfolder))
import faengine
from faengine import FAEngine

testdatafolder=libfolder / 'testing' / 'testdata'
sfxfiles = list(testdatafolder.glob('*.sfx'))

class TestSingleSFXData:
    

    def test_version(self):
        assert isinstance(faengine.__version__, str)
    
    def test_single_file(self):
        ds = xr.open_dataset(filename_or_obj=sfxfiles[0],
                     engine=FAEngine)

        assert isinstance(ds, type(xr.Dataset()))
        assert len(ds.dims) == 4
        assert len(ds['t'].data) == 1
        assert 't' in list(ds.indexes)
        assert 'long_name' in ds['t'].attrs
        assert 'units' in ds[list(ds.variables)[55]].attrs
        assert "K" == ds['SFX.T2M'].attrs['units']
        assert len(ds.variables) > 900 #equal test might be too strickt?
        assert 'proj_crs' in ds.attrs.keys()


    def test_netcdf_complient(self):
        dummy_path = testdatafolder.joinpath('deleteme.nc')
        if dummy_path.exists():
            dummy_path.unlink()
        
        ds = xr.open_dataset(filename_or_obj=sfxfiles[0],
                     engine=FAEngine,
                      backend_kwargs={
                         'whitefield_glob':'*2M'}
        )

        ds.to_netcdf(dummy_path) #this tests the decoding

        ds2 = xr.open_dataset(dummy_path)

        assert list(ds2.variables) == list(ds.variables)
        assert list(ds2.dims) == list(ds.dims)
        assert list(ds2.attrs) == list(ds.attrs)

        dummy_path.unlink()

                         

    def test_blacklist(self):
        ds = xr.open_dataset(filename_or_obj=sfxfiles[0],
                     engine=FAEngine,
                      backend_kwargs={
                         'whitefield_glob':'*2M',
                         'blackfield_glob': '*Q2M'}
        )
        assert 'SFX.Q2M' not in list(ds.variables)



    def test_lonlatgrid(self):
        ds = xr.open_dataset(filename_or_obj=sfxfiles[0],
                     engine=FAEngine,
                      backend_kwargs={
                         'whitefield_glob':'*2M',
                         'blackfield_glob': '*Q2M'}
        )
        assert 'lat' in ds.variables
        assert 'lon' in ds.variables
        assert 'degrees_north' == ds['lat'].attrs['units']
        assert 'fill_value' in ds['lat'].attrs.keys()
        assert 'degrees_east' == ds['lon'].attrs['units']

        assert ds['lon'].shape == ds['lat'].shape == (48,54)
        assert int(ds['lon'].max()) == 51
        assert int(ds['lat'].max()) == 5

        
        ds2 = xr.open_dataset(filename_or_obj=sfxfiles[0],
                     engine=FAEngine,
                      backend_kwargs={
                         'whitefield_glob':'*2M',
                         'blackfield_glob': '*Q2M',
                         'add_latlon_coords': False}
        )
        assert 'lat' not in ds2.coords
        assert 'lon' not in ds2.coords

    def test_baseref_dim(self):
        ds = xr.open_dataset(filename_or_obj=sfxfiles[0],
                     engine=FAEngine,
                      backend_kwargs={
                         'whitefield_glob':'*2M',
                         'blackfield_glob': '*Q2M',
                         'create_base_dimension': True}
        )
        assert ds['t_base'].shape == (1,)
        assert 'standard_name' in ds['t_base'].attrs
        assert 't_base' in list(ds.indexes)

        ds2 = xr.open_dataset(filename_or_obj=sfxfiles[0],
                     engine=FAEngine,
                      backend_kwargs={
                         'whitefield_glob':'*2M',
                         'blackfield_glob': '*Q2M',
                         'create_base_dimension': False}
        )
        assert 't_base' not in ds2.coords



class TestMultiSFXData:
    

    
    
    def test_mfdataset(self):
       
        ds = xr.open_mfdataset(
                sfxfiles,
                engine=FAEngine,
                backend_kwargs={
                    'whitefield_glob':'*2M', 
                    'blackfield_glob': '*Q2M',
                    'create_base_dimension': True},
                combine='by_coords',
                # concat_dim='t',  # or 'ref_t' if that's your intended concat dimension
                # join='exact',
                )
        ds

        
        
        assert isinstance(ds, type(xr.Dataset()))
        assert len(ds.dims) == 4
        assert len(ds['t'].data) == len(sfxfiles)
        assert 't' in list(ds.indexes)
        assert 'long_name' in ds['t'].attrs
        assert "K" == ds['SFX.T2M'].attrs['units']
        assert 'proj_crs' in ds.attrs.keys()
        



