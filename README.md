# icon_eu_eps
Download and plot ICON-EU-EPS data from DWD opendata server.

In the following repository I include a fully-functional suite of scripts 
needed to download, merge and plot data from the ICON-EU-EPS model,
which is freely available at https://opendata.dwd.de/weather/.

The main script to be called (possibly through cronjob) is `copy_data.run`. 
There, the current run version is determined, and files are downloaded from the DWD server.
Note that the grib2 are then directly read into the plotting funcions without doing any preprocessing. 
We use `pygrib` to read the data. All the functions used to read thed data are defined in `reader.py` 

This script was not maintained so it contains a lot of outdated functions. Need to change the parallelizing of plotting and downloading. 
