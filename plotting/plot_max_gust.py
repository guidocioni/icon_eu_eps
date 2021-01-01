import numpy as np
from multiprocessing import Pool
from functools import partial
from utils import *
import sys

debug = False
if not debug:
    import matplotlib
    matplotlib.use('Agg')

import matplotlib.pyplot as plt

# The one employed for the figure name when exported 
variable_name = 'prob_winds'

print_message('Starting script to plot '+variable_name)

# Get the projection as system argument from the call so that we can 
# span multiple instances of this script outside
if not sys.argv[1:]:
    print_message(
        'Projection not defined, falling back to default (euratl)')
    projection = 'euratl'
else:
    projection = sys.argv[1]

thresholds = [50]

def main():
    dset = read_dataset()

    dset['VMAX_10M'].metpy.convert_units('kph')

    for threshold in thresholds:
        ds = ((dset['VMAX_10M'] > threshold).sum(dim='realization') / 40)*100
        ds.attrs['threshold'] = threshold
        ds['run'] = dset['run']

        _ = plt.figure(figsize=(figsize_x, figsize_y))

        ax = plt.gca()
        m, x, y = get_projection(dset, projection, labels=True)
        m.fillcontinents(color='lightgray',lake_color='whitesmoke', zorder=0)

        # All the arguments that need to be passed to the plotting function
        args=dict(x=x, y=y, ax=ax)

        print_message('Pre-processing finished, launching plotting scripts')
        if debug:
            plot_files(dset.isel(time=slice(0, 2)), **args)
        else:
            # Parallelize the plotting by dividing into chunks and processes
            dss = chunks_dataset(ds, chunks_size)
            plot_files_param = partial(plot_files, **args)
            p = Pool(processes)
            p.map(plot_files_param, dss)


def plot_files(dss, **args):
    first = True
    for time_sel in dss.time:
        data = dss.sel(time=time_sel)
        time, run, cum_hour = get_time_run_cum(data)
        # Build the name of the output image
        filename = subfolder_images[projection] + '/' + variable_name + '_%s_%s.png' % (data.attrs['threshold'], cum_hour)

        cmap = plt.get_cmap('gist_stern_r')
        new_cmap = truncate_colormap(cmap, 0, 0.9)

        cs = args['ax'].tricontourf(args['x'], args['y'],
                                    data.values,
                                    extend='max',
                                    cmap=new_cmap,
                                    levels=np.linspace(10, 100, 10))

        an_fc = annotation_forecast(args['ax'], time)
        an_var = annotation(args['ax'], 'Prob. wind gust exceeding %s km/h' % data.attrs['threshold'], loc='lower left', fontsize=6)
        an_run = annotation_run(args['ax'], run)
        logo = add_logo_on_map(ax=args['ax'], zoom=0.1, pos=(0.95, 0.08))

        if first:
            plt.colorbar(cs, orientation='horizontal', label='Probability [%]',
                         fraction=0.04, pad=0.04)
        if debug:
            plt.show(block=True)
        else:
            plt.savefig(filename, **options_savefig)

        remove_collections([cs, an_fc, an_var, an_run, logo])

        first = False


if __name__ == "__main__":
    import time
    start_time=time.time()
    main()
    elapsed_time=time.time()-start_time
    print_message("script took " + time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))