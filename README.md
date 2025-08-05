# FAengine

The aim of this package is to allow a user to seamlessly use xarray for FA files. 
If you do not know what FA files are, then this package is of no use to you.

The actual reading of the FA files is done by Epygram. 

In practice, the core of this package is the FAEngine. This engine must be passed
to xarray, so that xarray knows how to open FA files. 



# Installation

For users, via pip install:


```shell
pip install git+https://github.com/vergauwenthomas/FAengine.git
```

For contributors, via git clone.


# Usage

To use the `FAEngine`, import this package, use xarray to open your target FA files,
pass the `FAEngine` to the `engine` argument, and you are ready to go. 

Extra arguments specific to the `FAEngine` can be provided using the `backend_kwargs` (see example).

```python
import xarray as xr
from faengine import FAEngine

# Get the path to the target FA file
path_to_FA = '/home/.../ICMSH...'

ds = xr.open_dataset(filename_or_obj=path_to_FA,
                     engine=FAEngine, # Pass the FAEngine here!
                     # Extra specific arguments for FA files:
                     backend_kwargs = {
                        # pass here the extra arguments
                        'whitefield_glob': '*2M',  # glob expression for all targeted fields
                        'blackfield_glob': '*Q2M',
                        'add_latlon_coords': True, # Set to True when merging cycles, typical for NWP
                        'create_base_dimension': True, 
                     } 
                    )
ds
```
Or if you want to open and combine multiple FA files:

```python
# Get the path to the directory containing FA files
Fa_dir = Path('/home/...')

# Get a list of all FA files
Fa_file_list = Fa_dir.glob('ICMSC*.SFX')


# Open them in xarray
ds = xr.open_mfdataset(Fa_file_list,
                     engine=FAEngine, # Pass the FAEngine here!
                     # Extra specific arguments for FA files:
                     backend_kwargs = {
                        # pass here the extra arguments
                        'whitefield_glob': '*2M',  # glob expression for all targeted fields
                        'blackfield_glob': '*Q2M',
                        'add_latlon_coords': True, # Set to True when merging cycles, typical for NWP
                        'create_base_dimension': True, 
                     },
                     combine='by_coords' #!!
                    )
ds

```
                     },
                     combine='by_coords' #!!  
                    )
ds

```

