import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.dates import  DateFormatter
from reader import read_coordinates, read_variable, read_dates
import seaborn as sns
import matplotlib.dates as mdates
from matplotlib.dates import  DateFormatter
from geopy.geocoders import Nominatim
import os

# Get coordinates 
lats, lons = read_coordinates()

# Get files list
main_folder='/scratch/local1/m300382/icon_eps/'
file_prefix='icon-eps_global_icosahedral'
level_type='single-level'
run=str(os.environ.get('run'))
diri_images='/scratch/local1/m300382/icon_eps/'

t2m = read_variable(variable='t_2m')
time= read_dates()
t2m = t2m-273.15
u10m = read_variable(variable='u_10m')
v10m = read_variable(variable='v_10m')
wind_speed=np.sqrt(u10m**2+v10m**2)
wind_speed=wind_speed*3.6

tot_prec = read_variable(variable='tot_prec')

cities = ["Hamburg"]

nrows=4
ncols=1
sns.set(style="white")

t_2m_point={}
tot_prec_point={}
wind_speed_10m_point={}

geolocator = Nominatim()
for city in cities:
    loc = geolocator.geocode(city)
    distance = np.sqrt((lats-loc.latitude)**2+(lons-loc.longitude)**2)
    ncell = np.argmin(distance)
    t_2m_point[city] = t2m[:,:,ncell]
    tot_prec_point[city] = tot_prec[:,:,ncell]
    wind_speed_10m_point[city] = wind_speed[:,:,ncell]
    
    fig = plt.figure(1, figsize=(10,12))
   
    ax1=plt.subplot2grid((nrows,ncols), (0,0))
    ax1.set_title("ICON-EPS meteogram for "+city+" | Run "+run)
    bplot=ax1.boxplot(t_2m_point[city].T, patch_artist=True, showfliers=False)
    for box in bplot['boxes']:
        box.set(color='LightBlue')
        box.set(facecolor='LightBlue')

    xaxis=np.arange(1,np.shape(time)[0]+1,1)
    ax1.plot(xaxis, np.mean(t_2m_point[city], axis=1), linewidth=1,color='red')
    ax1.set_ylabel("2m Temp. [C]",fontsize=8)
    ax1.yaxis.grid(True)
    ax1.tick_params(axis='y', which='major', labelsize=8)
    ax1.tick_params(axis='x', which='both', bottom=False)

    ax2=plt.subplot2grid((nrows,ncols), (1,0))
    bplot_rain=ax2.boxplot(tot_prec_point[city].T, patch_artist=True, showfliers=False)
    for box in bplot_rain['boxes']:
        box.set(color='LightBlue')
        box.set(facecolor='LightBlue')
    ax2.plot(xaxis, np.mean(tot_prec_point[city], axis=1), linewidth=1,color='red')
    ax2.set_ylim(bottom=0)
    ax2.yaxis.grid(True)
    ax2.set_ylabel("Precipitation [mm]",fontsize=8)
    ax2.tick_params(axis='y', which='major', labelsize=8)

    ax3=plt.subplot2grid((nrows,ncols), (2,0))
    bplot_wind=ax3.boxplot(wind_speed_10m_point[city].T, patch_artist=True,showfliers=False)
    for box in bplot_wind['boxes']:
        box.set(color='LightBlue')
        box.set(facecolor='LightBlue')
    ax3.plot(xaxis, np.mean(wind_speed_10m_point[city], axis=1), linewidth=1,color='red')
    ax3.yaxis.grid(True)
    ax3.set_ylabel("Wind speed [km/h]",fontsize=8)
    ax3.tick_params(axis='y', which='major', labelsize=8)
    ax3.set_ylim(bottom=0)
    
    ax4=plt.subplot2grid((nrows,ncols), (3,0))
    ax4.plot_date(time, t_2m_point[city], '-',linewidth=0.8)
    ax4.set_xlim(time[0],time[-1])
    ax4.set_ylabel("2m Temp. [C]",fontsize=8)
    ax4.tick_params(axis='y', which='major', labelsize=8)
    ax4.yaxis.grid(True)
    ax4.xaxis.grid(True)
    ax4.xaxis.set_major_locator(mdates.DayLocator())
    ax4.xaxis.set_major_formatter(DateFormatter('%d/%m/%y %HZ'))
    
    ax4.annotate('Grid point %4.2fN %4.2fE' % (lats[ncell], lons[ncell]), 
                 xy=(0.7, -0.7), xycoords='axes fraction', color="gray")
    
    fig.subplots_adjust(hspace=0.1)
    fig.autofmt_xdate()
    plt.savefig(diri_images+"meteogram_"+city, dpi=150, bbox_inches='tight')
    plt.clf()