import numpy as np
from reader import *
from config import *
import pandas as pd
import xarray as xr
import datetime

def wind_power(wind, a, b, c):
    return a/(1+np.exp(-b*(wind+c)))

dset = xr.merge([read_variable_xr(variable='u_10m'), read_variable_xr(variable='v_10m')])
dset1 = read_variable_xr(variable='t_2m')

lats, lons = read_coordinates()
time = pd.to_datetime(dset.valid_time.data)

wind = (dset.u10**2+dset.v10**2)**(0.5)
temperature = dset1.t2m - 273.15

# Using the parameters obtained by the fit
power = wind_power(wind, 2500.,  0.85, -7.5)

outdset = xr.Dataset({
         'wind_power': (['time', 'ensemble', 'ncell'],  power.values, {'units' : 'MW'} ),
         '2m Temperature':(['time', 'ensemble', 'ncell'],  temperature.values, {'units' : 'C'} ),
         'latitude'   : (['ncell'],  lats),
         'longitude'  : (['ncell'],  lons),
         },
         coords={'time': time, 'ensemble': dset.number.values , 'ncell' : np.arange(1,dset.dims['values']+1,1)},
         attrs={'creation date': datetime.datetime.now().strftime("%d %b %Y at %H:%M"),
                'author' : 'Guido Cioni (guido.cioni@mpimet.mpg.de)',
                'description' : 'Wind power prediction'})

outdset.to_netcdf('energy_sources.nc')

# time, n_ens, n_cell

# To be added plot of the average and standard deviation