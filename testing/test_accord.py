import pytest
import sys
from pathlib import Path


import xarray as xr



libfolder = Path(str(Path(__file__).resolve())).parent.parent

# point to current version of the faengine
sys.path.insert(1, str(libfolder))
import faengine
from faengine import FAEngine

testdatafolder=libfolder / 'testing' / 'testdata'

atmfiles = [testdatafolder.joinpath('ICMSHCSMK+0006h00m00s'),
            testdatafolder.joinpath('ICMSHCSMK+0005h00m00s')]
lbcfile = testdatafolder.joinpath('be70c_l_01') #THIS IS AN OLD FILE
pgdfile = testdatafolder.joinpath('Const.Clim.09')

class TestLBCData:

   def test_open_file(self):
      ds = xr.open_dataset(filename_or_obj=lbcfile,
                     engine=FAEngine)
        

class TestATMData:
   def test_open_file(self):
         
      ds = xr.open_dataset(filename_or_obj=atmfiles[0],
                  engine=FAEngine,
                  backend_kwargs={
                     'whitefield_glob':'*TKE*',
                     'blackfield_glob': 'CLS*'}
                  )
      assert isinstance(ds, type(xr.Dataset()))
      assert len(ds.dims) == 5
      assert len(ds['TKE'].dims) == 5
      assert 'proj_crs' in ds.attrs.keys()
      assert ds.attrs['PGD_detected'] == 'False'
      assert ds.attrs['zdim_detected'] == 'True'
      
   def test_netcdf_complient(self):
      dummy_path = testdatafolder.joinpath('deleteme_atm.nc')
      if dummy_path.exists():
         dummy_path.unlink()
      ds = xr.open_dataset(filename_or_obj=atmfiles[0],
                  engine=FAEngine,
                  backend_kwargs={
                     'whitefield_glob':'*TKE*',
                     'blackfield_glob': 'CLS*'}
                  )
      assert isinstance(ds, type(xr.Dataset()))
      
      ds.to_netcdf(dummy_path) #this tests the decoding
      ds2 = xr.open_dataset(dummy_path)

      assert list(ds2.variables) == list(ds.variables)
      assert list(ds2.dims) == list(ds.dims)
      assert list(ds2.attrs) == list(ds.attrs)
      assert list(ds2['TKE'].dims) == list(ds['TKE'].dims)
      assert list(ds2['TKE'].attrs) == list(ds['TKE'].attrs)

      dummy_path.unlink()


      
    

class TestPGDData:
     def test_open_file(self):
         ds = xr.open_dataset(filename_or_obj=pgdfile,
                     engine=FAEngine)
        
         assert isinstance(ds, type(xr.Dataset()))
         assert len(ds.dims) == 2 #NO TIME DETAILS
        
         assert len(ds.variables) > 30 #equal test might be too strickt?
         assert 'proj_crs' in ds.attrs.keys()
         assert ds.attrs['PGD_detected'] == 'True'
         assert ds.attrs['zdim_detected'] == 'False'