import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reader import read_coordinates, read_dates, read_variable
from config import folder_images, get_projection, dpi_resolution, n_members_ensemble, annotation_run, annotation, truncate_colormap
import pandas as pd

lats, lons = read_coordinates()
time=read_dates()
cum_hour=np.array((time-time[0]) / pd.Timedelta('1 hour')).astype("int")

t2m = read_variable(variable='t_2m')
t2m = t2m-273.15

# Compute arrays to plot just once

t2m_std=t2m.std(axis=0)
t2m_mean=t2m.mean(axis=0)
t2m_std=np.ma.masked_less_equal(t2m_std, 1)

# Truncate colormap
cmap = plt.get_cmap('Greys')
new_cmap = truncate_colormap(cmap, 0.1, 0.9)

levels=(-15, -10, -5, 0, 5, 10, 15, 20)
levels_std=np.linspace(0, round(t2m_std.max()), 16)

# Euro-Atlantic plots
fig = plt.figure(figsize=(11,7))
m = get_projection("europe")
x, y = m(lons,lats)
m.shadedrelief(scale=0.4, alpha=0.8)

first = True
for i, date in enumerate(time):
    c = m.contour(lons, lats, t2m_mean[i,:], extend='both', levels=levels, tri=True)
    cs = m.contourf(lons, lats,t2m_std[i,:], extend='both', levels=levels_std,
                    cmap=new_cmap, tri=True)
    
    labels=plt.gca().clabel(c, c.levels, inline=True, fmt='%d' , fontsize=10)
    plt.title('Forecast for %s' % date.strftime('%d %b %Y at %H UTC'))
    annotation_run(plt.gca(), time)
    annotation(plt.gca(), text='ICON-EU-EPS', loc='upper left')
    annotation(plt.gca(), text='www.guidocioni.it', loc='lower right')
    
    if first: # Apparently it only needs to be added once...
        plt.colorbar(cs, orientation='horizontal', label='Standard deviation [C]', pad=0.03, fraction=0.04)
    plt.savefig(folder_images+'t2m_%s.png' % cum_hour[i],
                dpi=dpi_resolution, bbox_inches='tight')
    # This is needed to have contour which not overlap
    for coll in c.collections: 
        coll.remove()
    for coll in cs.collections: 
        coll.remove()
    for label in labels:
        label.remove()
    first=False