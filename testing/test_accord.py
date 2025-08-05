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


lbcfile = testdatafolder.joinpath('be70c_l_01')
pgdfile = testdatafolder.joinpath('Const.Clim.09')

# class TestLBCData:
#      def test_open_file(self):
#         ds = xr.open_dataset(filename_or_obj=lbcfile,
#                      engine=FAEngine)
        

class TestPGDData:
     def test_open_file(self):
         ds = xr.open_dataset(filename_or_obj=pgdfile,
                     engine=FAEngine)
        
         assert isinstance(ds, type(xr.Dataset()))
         assert len(ds.dims) == 2 #NO TIME DETAILS
        
         assert len(ds.variables) > 30 #equal test might be too strickt?
         assert 'proj_crs' in ds.attrs.keys()
         assert ds.attrs['PGD_detected'] == 'True'