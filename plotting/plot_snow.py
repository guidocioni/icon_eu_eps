import matplotlib.pyplot as plt
import numpy as np
from multiprocessing import Pool
from functools import partial
import utils
import sys
import xarray as xr

debug = False
if not debug:
    import matplotlib
    matplotlib.use('Agg')


# The one employed for the figure name when exported
variable_name = 'prob_snow'

utils.print_message('Starting script to plot '+variable_name)

# Get the projection as system argument from the call so that we can
# span multiple instances of this script outside
if not sys.argv[1:]:
    utils.print_message(
        'Projection not defined, falling back to default (euratl)')
    projection = 'euratl'
else:
    projection = sys.argv[1]


def main():
    dset = utils.read_dataset(
        ['snow_gsp', 'snow_con', 'tot_prec'], region=projection)

    snow_acc = dset['csrwe'] + dset['lssrwe']
    snow = snow_acc.differentiate(coord="step", datetime_unit="h")
    rain = dset['tp'].differentiate(coord="step", datetime_unit="h")

    dset['snow_prob'] = ((snow > 0.25).sum(
        dim='number') / len(dset.number)) * 100
    dset['prec_prob'] = ((rain > 0.1).sum(
        dim='number') / len(dset.number)) * 100

    levels = np.linspace(10, 100, 10)

    cmap_snow, norm_snow = utils.get_colormap_norm("snow", levels)
    cmap_rain, norm_rain = utils.get_colormap_norm("rain", levels)

    _ = plt.figure(figsize=(utils.figsize_x, utils.figsize_y))

    ax = plt.gca()
    m, x, y = utils.get_projection(dset, projection, labels=True)
    m.fillcontinents(color='lightgray', lake_color='whitesmoke', zorder=0)

    dset = dset.drop(['csrwe', 'lssrwe', 'tp', 'clon', 'clat']).load()

    # All the arguments that need to be passed to the plotting function
    args = dict(x=x, y=y, ax=ax, cmap_snow=cmap_snow, norm_snow=norm_snow,
                cmap_rain=cmap_rain, norm_rain=norm_rain, levels=levels)

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
                                    data['prec_prob'],
                                    extend='max',
                                    cmap=args['cmap_rain'],
                                    norm=args['norm_rain'],
                                    levels=args['levels'],
                                    zorder=1)

        css = args['ax'].tricontourf(args['x'],
                                     args['y'],
                                     data['snow_prob'],
                                     extend='max',
                                     cmap=args['cmap_snow'],
                                     norm=args['norm_snow'],
                                     levels=args['levels'],
                                     zorder=2)

        an_fc = utils.annotation_forecast(args['ax'], time)
        an_var = utils.annotation(
            args['ax'], 'Prob. snow rate > 0.25 mm/h & rain rate > 0.1 mm/h', loc='lower left', fontsize=6)
        an_run = utils.annotation_run(args['ax'], run)

        if first:
            if projection == "euratl":
                x_cbar_0, y_cbar_0, x_cbar_size, y_cbar_size = 0.15, 0.15, 0.35, 0.02
                x_cbar2_0, y_cbar2_0, x_cbar2_size, y_cbar2_size = 0.55, 0.15, 0.35, 0.02
            elif projection == "de":
                x_cbar_0, y_cbar_0, x_cbar_size, y_cbar_size = 0.17, 0.05, 0.32, 0.02
                x_cbar2_0, y_cbar2_0, x_cbar2_size, y_cbar2_size = 0.55, 0.05, 0.32, 0.02
            elif projection == "it":
                x_cbar_0, y_cbar_0, x_cbar_size, y_cbar_size = 0.18, 0.05, 0.3, 0.02
                x_cbar2_0, y_cbar2_0, x_cbar2_size, y_cbar2_size = 0.55, 0.05, 0.3, 0.02
            ax_cbar = plt.gcf().add_axes(
                [x_cbar_0, y_cbar_0, x_cbar_size, y_cbar_size])
            ax_cbar_2 = plt.gcf().add_axes(
                [x_cbar2_0, y_cbar2_0, x_cbar2_size, y_cbar2_size])
            cbar_snow = plt.gcf().colorbar(css, cax=ax_cbar, orientation='horizontal',
                                           label='Snow [cm/hr]')
            cbar_rain = plt.gcf().colorbar(cs, cax=ax_cbar_2, orientation='horizontal',
                                           label='Rain [mm/hr]')
            cbar_snow.ax.tick_params(labelsize=8)
            cbar_rain.ax.tick_params(labelsize=8)

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
    utils.print_message(
        "script took " + time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))
