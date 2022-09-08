import matplotlib.pyplot as plt
import numpy as np
from multiprocessing import Pool
from functools import partial
import utils
import sys

debug = False
if not debug:
    import matplotlib
    matplotlib.use('Agg')


# The one employed for the figure name when exported
variable_name = 'prob_clouds'

utils.print_message('Starting script to plot '+variable_name)

# Get the projection as system argument from the call so that we can
# span multiple instances of this script outside
if not sys.argv[1:]:
    utils.print_message(
        'Projection not defined, falling back to default (de)')
    projection = 'de'
else:
    projection = sys.argv[1]


def main():
    dset = utils.read_dataset(['clct'], region=projection)
    dset['prob_cloudy'] = ((dset.CLCT > 50).sum(
        dim='number') / len(dset.number)) * 100

    levels = np.linspace(10, 100, 10)
    cmap = utils.get_colormap("sky")

    _ = plt.figure(figsize=(utils.figsize_x, utils.figsize_y))

    ax = plt.gca()
    m, x, y = utils.get_projection(dset, projection, labels=True)
    m.fillcontinents(color='lightgray', lake_color='whitesmoke', zorder=0)

    dset = dset.drop(['CLCT','clon','clat']).load()

    # All the arguments that need to be passed to the plotting function
    args = dict(x=x, y=y, ax=ax, levels=levels, cmap=cmap)

    utils.print_message('Pre-processing finished, launching plotting scripts')
    if debug:
        plot_files(dset.isel(step=slice(0, 2)), **args)
    else:
        # Parallelize the plotting by dividing into chunks and processes
        dss = utils.chunks_dataset(dset, utils.chunks_size)
        plot_files_param = partial(plot_files, **args)
        p = Pool(utils.processes)
        p.map(plot_files_param, dss)


def plot_files(dss, **args):
    first = True
    for time_sel in dss.step:
        data = dss.sel(step=time_sel)
        time, run, cum_hour = utils.get_time_run_cum(data)
        # Build the name of the output image
        filename = utils.subfolder_images[projection] + \
            '/' + variable_name + '_%s.png' % cum_hour

        cs = args['ax'].tricontourf(args['x'],
                                    args['y'],
                                    data['prob_cloudy'],
                                    extend='both',
                                    cmap=args['cmap'],
                                    levels=args['levels'])

        an_fc = utils.annotation_forecast(args['ax'], time)
        an_var = utils.annotation(
            args['ax'], 'Prob. cloud cover > 50%', loc='lower left', fontsize=6)
        an_run = utils.annotation_run(args['ax'], run)

        if first:
            plt.colorbar(cs, orientation='horizontal', label='Probability [%]',
                         fraction=0.04, pad=0.04)

        if debug:
            plt.show(block=True)
        else:
            plt.savefig(filename, **utils.options_savefig)

        utils.remove_collections([cs, an_fc, an_var, an_run])

        first = False


if __name__ == "__main__":
    import time
    start_time = time.time()
    main()
    elapsed_time = time.time()-start_time
    utils.print_message("script took " + time.strftime("%H:%M:%S",
                                                       time.gmtime(elapsed_time)))
