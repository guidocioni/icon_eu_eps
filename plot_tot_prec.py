import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reader import read_coordinates, read_dates, read_variable
from config import folder_images, get_projection, dpi_resolution, n_members_ensemble, annotation_run, annotation, truncate_colormap
import pandas as pd

# Get coordinates 
lats, lons = read_coordinates()
time=read_dates()
cum_hour=np.array((time-time[0]) / pd.Timedelta('1 hour')).astype("int")

tot_prec=read_variable(variable='tot_prec')
# time, n_ens, n_cell

# Probabilites plot 
thresholds = [50.]

fig = plt.figure(figsize=(11,7))
m = get_projection("europe")
x, y = m(lons,lats)
m.shadedrelief(scale=0.4, alpha=0.8)

# Truncate colormap
cmap = plt.get_cmap('gist_stern_r')
new_cmap = truncate_colormap(cmap, 0, 0.9)

first = True 
for threshold in thresholds:
    probabilities = (np.sum(tot_prec > threshold, axis=1)/float(n_members_ensemble))*100.
    probabilities = np.ma.masked_less_equal(probabilities, 10)
    
    for i, date in enumerate(time):
        cs = m.contourf(x, y, probabilities[i,:], levels=np.linspace(10, 100, 10),
         cmap=new_cmap, tri=True, extend='max')

        plt.title('Probability tot. prec. > '+str(int(threshold))+' mm | '+date.strftime('%d %b %Y at %H UTC'))
        annotation_run(plt.gca(), time)
        annotation(plt.gca(), text='ICON-EU-EPS', loc='upper left')
        annotation(plt.gca(), text='www.meteoindiretta.it', loc='lower right')

        if first: #
            plt.colorbar(cs, orientation='horizontal', label='Probability [%]',fraction=0.046, pad=0.04)
        plt.savefig(folder_images+'prob_prec_%s_%s.png' % (int(threshold), cum_hour[i]),
                    dpi=dpi_resolution, bbox_inches='tight')
        for coll in cs.collections: 
            coll.remove()
        first=False

plt.close('all')

# To be added plot of the average and standard deviation