import time
from tqdm.contrib.concurrent import process_map
import sys
from utils import get_city_coordinates, read_dataset, processes, folder_images, convert_timezone
import matplotlib.dates as mdates
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec
import pandas as pd
import matplotlib
matplotlib.use('Agg')


print('Starting script to plot meteograms')

# Get the projection as system argument from the call so that we can
# span multiple instances of this script outside
if not sys.argv[1:]:
    print('City not defined, falling back to default (Hamburg)')
    cities = ['Hamburg']
else:
    cities = sys.argv[1:]


def main():
    ds = read_dataset(vars=['t_2m', 'tot_prec',
                            'snow_gsp', 'snow_con', 'clct'])
    ds['snow_rate'] = (ds['lssrwe'] + ds['csrwe']).differentiate(coord="step", datetime_unit="h")
    # we use total prec for this
    ds['rain_rate'] = ds['tp'].differentiate(coord="step", datetime_unit="h")

    lons, lats = np.deg2rad(ds.clon), np.deg2rad(ds.clat)

    it = []
    for city in cities:
        lon, lat = get_city_coordinates(city)
        # Find closest point with haversine distance
        dlon = np.deg2rad(lon) - lons
        dlat = np.deg2rad(lat) - lats
        a = np.sin(dlat/2.0)**2 + np.cos(lats) * \
            np.cos(np.deg2rad(lat)) * np.sin(dlon/2.0)**2
        c = 2 * np.arcsin(np.sqrt(a))
        km = 6367 * c
        sel = np.argmin(km.values)
        d = ds.drop(['lssrwe', 'csrwe','tp']).isel(cell=sel).compute()
        d.attrs['city'] = city
        it.append(d)

    process_map(plot, it, max_workers=processes, chunksize=2)


def plot(dset_city):
    city = dset_city.attrs['city']
    print('Producing meteogram for %s' % city)
    dset_city['t2m'] = dset_city['t2m'].metpy.convert_units('degC').metpy.dequantify()
    dset_city['valid_time'] = convert_timezone(
        pd.to_datetime(dset_city.valid_time))

    nrows = 3
    ncols = 1
    sns.set(style="white")

    locator = mdates.AutoDateLocator(minticks=12, maxticks=36)
    formatter = mdates.ConciseDateFormatter(locator,
                                            show_offset=False,
                                            formats=['%y', '%a %d %b', '%a %d %b', '%H EST', '%H EST', '%S'])

    fig = plt.figure(1, figsize=(9, 10))
    gs = gridspec.GridSpec(nrows, ncols, height_ratios=[1, 1, 1])

    ax_temp = plt.subplot(gs[0])
    ax_temp.set_title("ICON-EU-EPS meteogram for "+city+" | Run " +
                      dset_city.time.dt.strftime('%Y%m%d %H UTC').item())
    ax_temp.plot(dset_city['valid_time'],
                 dset_city['t2m'].values.T, '-', linewidth=0.8, zorder=1)
    ax_temp.set_xlim(dset_city['valid_time'][0], dset_city['valid_time'][-1])
    ax_temp.xaxis.set_major_locator(locator)
    ax_temp.xaxis.set_major_formatter(formatter)
    ax_temp.yaxis.grid(True)
    ax_temp.xaxis.grid(True, color='gray', linewidth=0.2)
    ax_temp.tick_params(axis='y', which='major', labelsize=8)
    ax_temp.tick_params(axis='x', which='both',
                        bottom=False, labelbottom=False)
    ax_temp.set_ylabel("2m temperature", fontsize=8)

    ax_prec = plt.subplot(gs[1])
    widths = np.concatenate([np.full(49, 0.035), np.full(8,0.1), np.full(8, 0.2)])
    for member in range(1, len(dset_city.number)):
        ax_prec.bar(dset_city['valid_time'],
                    dset_city.rain_rate.sel(number=member).values, width=widths,
                    alpha=0.2, color='blue', zorder=1)
        ax_prec.bar(dset_city['valid_time'],
                    dset_city.snow_rate.sel(number=member).values, width=widths,
                    alpha=0.2, color='purple', zorder=2)

    # Add text on top of the bars
    y_max = dset_city['rain_rate'].max(dim='number')
    x = dset_city['valid_time']
    prob = ((dset_city['rain_rate'] > 0.1).sum(
            dim='number') / len(dset_city.number)) * 100
    for i, _ in enumerate(prob):
        if prob[i] > 0:
            ax_prec.annotate(
                ("%d%%" % prob[i]),
                (x[i], y_max[i]),
                color='black',
                weight='bold',
                fontsize=6,
                zorder=5,
                horizontalalignment='center',
                rotation=90)

    ax_prec.yaxis.grid(True)
    ax_prec.xaxis.grid(True, color='gray', linewidth=0.2)
    ax_prec.set_ylim(bottom=0)
    ax_prec.set_xlim(dset_city['valid_time'][0], dset_city['valid_time'][-1])
    ax_prec.xaxis.set_major_locator(locator)
    ax_prec.xaxis.set_major_formatter(formatter)
    ax_prec.tick_params(axis='y', which='major', labelsize=8)
    ax_prec.tick_params(axis='x', which='both',
                        bottom=False, labelbottom=False)
    ax_prec.set_ylabel("Rain (blue) and snow (purple)", fontsize=8)

    ax_clouds = plt.subplot(gs[2])
    ax_clouds.plot(dset_city['valid_time'],
                   dset_city['CLCT'].values.T, 'o', zorder=1, markersize=5)
    ax_clouds.plot(dset_city['valid_time'], dset_city['CLCT'].mean(dim='number'), '-',
                   linewidth=2, zorder=2, color='black')
    ax_clouds.yaxis.grid(True)
    ax_clouds.xaxis.grid(True, color='gray', linewidth=0.2)
    ax_clouds.set_ylim(bottom=0)
    ax_clouds.set_xlim(dset_city['valid_time'][0], dset_city['valid_time'][-1])
    ax_clouds.xaxis.set_major_locator(locator)
    ax_clouds.xaxis.set_major_formatter(formatter)
    for label in ax_clouds.get_xticklabels(which='major'):
        label.set(rotation=90)
    ax_clouds.tick_params(axis='y', which='major', labelsize=8)
    ax_clouds.tick_params(axis='x', which='both', labelsize=8)
    ax_clouds.set_ylabel("Cloud cover", fontsize=8)

    ax_clouds.annotate('Grid point %3.1fN %3.1fE' % (dset_city.clat, dset_city.clon),
                       xy=(0.7, -0.4), xycoords='axes fraction', color="gray")


    fig.subplots_adjust(hspace=0.05)

    plt.savefig(folder_images+"meteogram_"+city, dpi=100, bbox_inches='tight')
    plt.clf()


if __name__ == "__main__":
    start_time = time.time()
    main()
    elapsed_time = time.time()-start_time
    print("script took " + time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))
