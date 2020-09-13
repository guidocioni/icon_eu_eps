# Configuration file for some common variables to all script 
from mpl_toolkits.basemap import Basemap  # import Basemap matplotlib toolkit
import numpy as np
from matplotlib.offsetbox import AnchoredText
import matplotlib.colors as colors

# Output folder for images 
folder_images = "/scratch/local1/m300382/icon_eu_eps/"
# Resolution of images 
dpi_resolution = 120
# Number of ensemble members
n_members_ensemble = 40

def get_projection(projection="euroatlantic", countries=True, regions=False, labels=False):
    if projection=="euroatlantic":
        m = Basemap(projection='mill', llcrnrlon=-50, llcrnrlat=30, urcrnrlon=30, urcrnrlat=70,resolution='i')
        m.drawcoastlines(linewidth=0.5, linestyle='solid', color='black')
        if countries:
            m.drawcountries(linewidth=0.5, linestyle='solid', color='black')
        if labels:
            m.drawparallels(np.arange(-90.0, 90.0, 10.), linewidth=0.2, color='white',
                labels=[True, False, False, True], fontsize=7)
            m.drawmeridians(np.arange(0.0, 360.0, 10.), linewidth=0.2, color='white',
                labels=[True, False, False, True], fontsize=7)
            
    elif projection=="europe":
        m = Basemap(projection='cyl', llcrnrlon=-15, llcrnrlat=29, urcrnrlon=35, urcrnrlat=71,resolution='i')
        m.drawcoastlines(linewidth=0.5, linestyle='solid', color='black')
        if countries:
            m.drawcountries(linewidth=0.5, linestyle='solid', color='black')
        if labels:
            m.drawparallels(np.arange(-90.0, 90.0, 10.), linewidth=0.2, color='white',
                labels=[True, False, False, True], fontsize=7)
            m.drawmeridians(np.arange(0.0, 360.0, 10.), linewidth=0.2, color='white',
                labels=[True, False, False, True], fontsize=7)            
            
    elif projection=="italy":
        m = Basemap(projection='cyl', llcrnrlon=6, llcrnrlat=36, urcrnrlon=18.5, urcrnrlat=48,  resolution='i')
        m.drawcoastlines()
        if countries:
            m.drawcountries()
        if regions:
            m.readshapefile('/home/mpim/m300382/shapefiles/ITA_adm_shp/ITA_adm1',
                            'ITA_adm1',linewidth=0.2,color='black')
        if labels:
            m.drawparallels(np.arange(-80.,81.,10), linewidth=0.2, labels=[True, False, False, True])
            m.drawmeridians(np.arange(-180.,181.,10), linewidth=0.2, labels=[True, False, False, True])
     
    return(m)

# Annotation run, models 
def annotation_run(ax, time, loc='upper right'):
    at = AnchoredText('Run %s'% time[0].strftime('%Y%m%d %H UTC'), 
                      prop=dict(size=8), frameon=True, loc=loc)
    at.patch.set_boxstyle("round,pad=0.,rounding_size=0.1")
    ax.add_artist(at)

def annotation(ax, text, loc='upper right'):
    at = AnchoredText('%s'% text, prop=dict(size=8), frameon=True, loc=loc)
    at.patch.set_boxstyle("round,pad=0.,rounding_size=0.1")
    ax.add_artist(at)

def truncate_colormap(cmap, minval=0.0, maxval=1.0, n=256):
    new_cmap = colors.LinearSegmentedColormap.from_list(
        'trunc({n},{a:.2f},{b:.2f})'.format(n=cmap.name, a=minval, b=maxval),
        cmap(np.linspace(minval, maxval, n)))
    return new_cmap