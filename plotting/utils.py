import numpy as np
from matplotlib.offsetbox import AnchoredText
import matplotlib.colors as colors
import pandas as pd
from matplotlib.colors import from_levels_and_colors
import seaborn as sns
import os
import matplotlib.patheffects as path_effects
import matplotlib.cm as mplcm
import sys
from glob import glob
import xarray as xr
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
import metpy
import re
from matplotlib.image import imread as read_png
import requests
import json

import warnings
warnings.filterwarnings(
    action='ignore',
    message='The unit of the quantity is stripped.'
)

apiKey = os.environ['MAPBOX_KEY']
apiURL_places = "https://api.mapbox.com/geocoding/v5/mapbox.places"

if 'MODEL_DATA_FOLDER' in os.environ:
    folder = os.environ['MODEL_DATA_FOLDER']
else:
    folder = '/home/ekman/ssd/guido/icon-eu-eps'

folder_images = folder
chunks_size = 10
processes = 2
figsize_x = 11
figsize_y = 9
invariant_file = folder+'invariant_*.nc'

if "HOME_FOLDER" in os.environ:
    home_folder = os.environ['HOME_FOLDER']
else:
    home_folder = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# Options for savefig
options_savefig = {
    'dpi':100,
    'bbox_inches':'tight',
    'transparent': False
}

# Dictionary to map the output folder based on the projection employed
subfolder_images = {
    'euratl' : folder_images,
    'it' : folder_images+'it',
    'de' : folder_images+'de'
}

folder_glyph = home_folder + '/plotting/yrno_png/'
WMO_GLYPH_LOOKUP_PNG = {
        '0': '01',
        '1': '02',
        '2': '02',
        '3': '04',
        '5': '15',
        '10': '15',
        '14': '15',
        '30': '15',
        '40': '15',
        '41': '15',
        '42': '15',
        '43': '15',
        '44': '15',
        '45': '15',
        '46': '15',
        '47': '15',
        '50': '46',
        '52': '46',
        '53': '46',
        '60': '09',
        '61': '09',
        '63': '10',
        '64': '41',
        '65': '12',
        '68': '47',
        '69': '48',
        '70': '13',
        '71': '49',
        '73': '50',
        '74': '45',
        '75': '48',
        '80': '05',
        '81': '05',
        '83': '41',
        '84': '32',
        '85': '08',
        '86': '34',
        '87': '45',
        '89': '43',
        '90': '30',
        '91': '30',
        '92': '25',
        '93': '33',
        '94': '34',
        '95': '25',
}

proj_defs = {
    'euratl':
    {
        'projection': 'mill',
        'llcrnrlon': -23.5,
        'llcrnrlat': 29.5,
        'urcrnrlon': 45,
        'urcrnrlat': 70.5,
        'resolution': 'l',
        'epsg': 4269
    },
    'it':
    {
        'projection': 'mill',
        'llcrnrlon': 6,
        'llcrnrlat': 36,
        'urcrnrlon': 19,
        'urcrnrlat': 48,
        'resolution': 'i',
        'epsg': 4269
    },
    'de':
    {
        'projection': 'cyl',
        'llcrnrlon': 5,
        'llcrnrlat': 46.5,
        'urcrnrlon': 16,
        'urcrnrlat': 56,
        'resolution': 'i',
        'epsg': 4269
    }
}


def read_dataset(vars=['tmax_2m', 'vmax_10m'],
                 region=None):
    """Wrapper to initialize the dataset"""
    dss = []
    for var in vars:
        dss.append(xr.open_mfdataset(f"{folder}/*{var}*.grib2"))
    dset = xr.merge(dss, compat='override')
    grid = xr.open_dataset(f"{folder}/icon_grid_0028_R02B07_N02.nc")
    dset = dset.assign_coords(
        {'values': grid.rename_dims({'cell': 'values'}).clat})
    dset['clon'] = np.rad2deg(dset['clon'])
    dset['clat'] = np.rad2deg(dset['clat'])
    dset = dset.chunk({'number': 1})
    dset = dset.metpy.parse_cf()

    if region:
        proj = proj_defs[region]
        min_lon, max_lon = proj['llcrnrlon'], proj['urcrnrlon']
        min_lat, max_lat = proj['llcrnrlat'], proj['urcrnrlat']
        dset = dset.where((dset.clon >= min_lon) & (dset.clat >= min_lat) & (
            dset.clat <= max_lat) & (dset.clon <= max_lon), drop=True)

    return dset


def get_time_run_cum(dset):
    time = dset['valid_time'].values
    run = dset['time'].values
    cum_hour = np.array(dset['step'].values /
                        pd.Timedelta('1 hour')).astype(int)

    return time, run, cum_hour


def print_message(message):
    """Formatted print"""
    print(os.path.basename(sys.argv[0])+' : '+message)


def get_coordinates(ds):
    """Get the lat/lon coordinates from the ds and convert them to degrees.
    Usually this is only used to prepare the plotting."""
    if ('tlat' in ds.variables.keys()) and ('tlon' in ds.variables.keys()):
        longitude = ds['tlon']
        latitude = ds['tlat']
    elif ('clat' in ds.variables.keys()) and ('clon' in ds.variables.keys()):
        longitude = ds['clon']
        latitude = ds['clat']

    if longitude.max() > 180:
        longitude = (((longitude.lon + 180) % 360) - 180)

    return longitude.values, latitude.values


def get_city_coordinates(city):
    # First read the local cache and see if we already downloaded the city coordinates
    if os.path.isfile(home_folder + '/plotting/cities_coordinates.csv'):
        cities_coords = pd.read_csv(home_folder + '/plotting/cities_coordinates.csv',
                                    index_col=[0])
        if city in cities_coords.index:
            return cities_coords.loc[city].lon, cities_coords.loc[city].lat
        else:
            # make the request and append to the file
            url = "%s/%s.json?&access_token=%s" % (apiURL_places, city, apiKey)
            response = requests.get(url)
            json_data = json.loads(response.text)
            lon, lat = json_data['features'][0]['center']
            to_append = pd.DataFrame(index=[city],
                                     data={'lon': lon, 'lat': lat})
            to_append.to_csv(home_folder + '/plotting/cities_coordinates.csv',
                             mode='a', header=False)

            return lon, lat
    else:
        # Make request and create the file for the first time
        url = "%s/%s.json?&access_token=%s" % (apiURL_places, city, apiKey)
        response = requests.get(url)
        json_data = json.loads(response.text)
        lon, lat = json_data['features'][0]['center']
        cities_coords = pd.DataFrame(index=[city],
                                     data={'lon': lon, 'lat': lat})
        cities_coords.to_csv(home_folder + '/plotting/cities_coordinates.csv')

        return lon, lat


def get_projection(dset, projection="euratl", countries=True, labels=True, regions=True):
    lon, lat = get_coordinates(dset)
    from mpl_toolkits.basemap import Basemap  # import Basemap matplotlib toolkit
    proj_options = proj_defs[projection]
    m = Basemap(**proj_options)
    if projection == "de":
        if regions:
            m.readshapefile(home_folder + '/plotting/shapefiles/DEU_adm/DEU_adm1',
                            'DEU_adm1', linewidth=0.2, color='black', zorder=5)
        if labels:
            m.drawparallels(np.arange(-80., 81., 2), linewidth=0.2, color='white',
                            labels=[True, False, False, True], fontsize=7)
            m.drawmeridians(np.arange(-180., 181., 2), linewidth=0.2, color='white',
                            labels=[True, False, False, True], fontsize=7)
    elif projection == "it":
        if regions:
            m.readshapefile(home_folder + '/plotting/shapefiles/ITA_adm/ITA_adm1',
                            'ITA_adm1', linewidth=0.2, color='black', zorder=5)
        if labels:
            m.drawparallels(np.arange(-80., 81., 2), linewidth=0.2, color='white',
                            labels=[True, False, False, True], fontsize=7)
            m.drawmeridians(np.arange(-180., 181., 2), linewidth=0.2, color='white',
                            labels=[True, False, False, True], fontsize=7)
    elif projection == "nord":
        if regions:
            m.readshapefile(home_folder + '/plotting/shapefiles/DEU_adm/DEU_adm1',
                            'DEU_adm1', linewidth=0.2, color='black', zorder=5)
        if labels:
            m.drawparallels(np.arange(-80., 81., 2), linewidth=0.2, color='white',
                            labels=[True, False, False, True], fontsize=7)
            m.drawmeridians(np.arange(-180., 181., 2), linewidth=0.2, color='white',
                            labels=[True, False, False, True], fontsize=7)

    m.drawcoastlines(linewidth=0.5, linestyle='solid', color='black', zorder=5)
    if countries:
        m.drawcountries(linewidth=0.5, linestyle='solid',
                        color='black', zorder=5)

    x, y = m(lon, lat)

    return (m, x, y)


def chunks_dataset(ds, n):
    """Same as 'chunks' but for the time dimension in
    a dataset"""
    for i in range(0, len(ds.step), n):
        yield ds.isel(step=slice(i, i + n))


# Annotation run, models
def annotation_run(ax, time, loc='upper right', fontsize=8):
    """Put annotation of the run obtaining it from the
    time array passed to the function."""
    time = pd.to_datetime(time)
    at = AnchoredText('Run %s' % time.strftime('%Y%m%d %H UTC'),
                      prop=dict(size=fontsize), frameon=True, loc=loc)
    at.patch.set_boxstyle("round,pad=0.,rounding_size=0.1")
    at.zorder = 10
    ax.add_artist(at)
    return (at)


def annotation_forecast(ax, time, loc='upper left', fontsize=8, local=True):
    """Put annotation of the forecast time."""
    time = pd.to_datetime(time)
    if local:  # convert to local time
        time = convert_timezone(time)
        at = AnchoredText('Valid %s' % time.strftime('%A %d %b %Y at %H (Berlin)'),
                          prop=dict(size=fontsize), frameon=True, loc=loc)
    else:
        at = AnchoredText('Forecast for %s' % time.strftime('%A %d %b %Y at %H UTC'),
                          prop=dict(size=fontsize), frameon=True, loc=loc)
    at.patch.set_boxstyle("round,pad=0.,rounding_size=0.1")
    at.zorder = 10
    ax.add_artist(at)
    return (at)


def add_logo_on_map(ax, logo=home_folder+'/plotting/meteoindiretta_logo.png', zoom=0.15, pos=(0.92, 0.1)):
    '''Add a logo on the map given a pnd image, a zoom and a position
    relative to the axis ax.'''
    img_logo = OffsetImage(read_png(logo), zoom=zoom)
    logo_ann = AnnotationBbox(
        img_logo, pos, xycoords='axes fraction', frameon=False)
    logo_ann.set_zorder(10)
    at = ax.add_artist(logo_ann)
    return at


def convert_timezone(dt_from, from_tz='utc', to_tz='Europe/Berlin'):
    """Convert between two timezones. dt_from needs to be a Timestamp 
    object, don't know if it works otherwise."""
    dt_to = dt_from.tz_localize(from_tz).tz_convert(to_tz)
    # remove again the timezone information
    return dt_to.tz_localize(None)


def annotation(ax, text, loc='upper right', fontsize=8):
    """Put a general annotation in the plot."""
    at = AnchoredText('%s' % text, prop=dict(
        size=fontsize), frameon=True, loc=loc)
    at.patch.set_boxstyle("round,pad=0.,rounding_size=0.1")
    at.zorder = 10
    ax.add_artist(at)
    return (at)


def truncate_colormap(cmap, minval=0.0, maxval=1.0, n=256):
    """Truncate a colormap by specifying the start and endpoint."""
    new_cmap = colors.LinearSegmentedColormap.from_list(
        'trunc({n},{a:.2f},{b:.2f})'.format(n=cmap.name, a=minval, b=maxval),
        cmap(np.linspace(minval, maxval, n)))
    return (new_cmap)


def get_colormap(cmap_type):
    """Create a custom colormap."""
    colors_tuple = pd.read_csv(
        home_folder + '/plotting/cmap_%s.rgba' % cmap_type).values

    cmap = colors.LinearSegmentedColormap.from_list(
        cmap_type, colors_tuple, colors_tuple.shape[0])
    return (cmap)


def get_colormap_norm(cmap_type, levels):
    """Create a custom colormap."""
    if cmap_type == "rain":
        cmap, norm = from_levels_and_colors(levels, sns.color_palette("Blues", n_colors=len(levels)),
                                            extend='max')
    elif cmap_type == "snow":
        cmap, norm = from_levels_and_colors(levels, sns.color_palette("PuRd", n_colors=len(levels)),
                                            extend='max')
    elif cmap_type == "snow_discrete":
        colors = ["#DBF069", "#5AE463", "#E3BE45", "#65F8CA", "#32B8EB",
                  "#1D64DE", "#E97BE4", "#F4F476", "#E78340", "#D73782", "#702072"]
        cmap, norm = from_levels_and_colors(levels, colors, extend='max')
    elif cmap_type == "rain_acc":
        cmap, norm = from_levels_and_colors(levels, sns.color_palette('gist_stern_r', n_colors=len(levels)),
                                            extend='max')
    elif cmap_type == "rain_new":
        colors_tuple = pd.read_csv(
            home_folder + '/plotting/cmap_prec.rgba').values
        cmap, norm = from_levels_and_colors(levels, sns.color_palette(colors_tuple, n_colors=len(levels)),
                                            extend='max')
    elif cmap_type == "winds":
        colors_tuple = pd.read_csv(
            home_folder + '/plotting/cmap_winds.rgba').values
        cmap, norm = from_levels_and_colors(levels, sns.color_palette(colors_tuple, n_colors=len(levels)),
                                            extend='max')

    return (cmap, norm)


def remove_collections(elements):
    """Remove the collections of an artist to clear the plot without
    touching the background, which can then be used afterwards."""
    for element in elements:
        try:
            for coll in element.collections:
                coll.remove()
        except AttributeError:
            try:
                for coll in element:
                    coll.remove()
            except ValueError:
                print_message('WARNING: Element is empty')
            except TypeError:
                element.remove()
        except ValueError:
            print_message('WARNING: Collection is empty')


def plot_maxmin_points(ax, lon, lat, data, extrema, nsize, symbol, color='k',
                       random=False):
    """
    This function will find and plot relative maximum and minimum for a 2D grid. The function
    can be used to plot an H for maximum values (e.g., High pressure) and an L for minimum
    values (e.g., low pressue). It is best to used filetered data to obtain  a synoptic scale
    max/min value. The symbol text can be set to a string value and optionally the color of the
    symbol and any plotted value can be set with the parameter color
    lon = plotting longitude values (2D)
    lat = plotting latitude values (2D)
    data = 2D data that you wish to plot the max/min symbol placement
    extrema = Either a value of max for Maximum Values or min for Minimum Values
    nsize = Size of the grid box to filter the max and min values to plot a reasonable number
    symbol = String to be placed at location of max/min value
    color = String matplotlib colorname to plot the symbol (and numerica value, if plotted)
    plot_value = Boolean (True/False) of whether to plot the numeric value of max/min point
    The max/min symbol will be plotted on the current axes within the bounding frame
    (e.g., clip_on=True)
    """
    from scipy.ndimage.filters import maximum_filter, minimum_filter

    # We have to first add some random noise to the field, otherwise it will find many maxima
    # close to each other. This is not the best solution, though...
    if random:
        data = np.random.normal(data, 0.2)

    if (extrema == 'max'):
        data_ext = maximum_filter(data, nsize, mode='nearest')
    elif (extrema == 'min'):
        data_ext = minimum_filter(data, nsize, mode='nearest')
    else:
        raise ValueError('Value for hilo must be either max or min')

    mxy, mxx = np.where(data_ext == data)
    # Filter out points on the border
    mxx, mxy = mxx[(mxy != 0) & (mxx != 0)], mxy[(mxy != 0) & (mxx != 0)]

    texts = []
    for i in range(len(mxy)):
        texts.append(ax.text(lon[mxy[i], mxx[i]], lat[mxy[i], mxx[i]], symbol, color=color, size=15,
                             clip_on=True, horizontalalignment='center', verticalalignment='center',
                             path_effects=[path_effects.withStroke(linewidth=1, foreground="black")], zorder=6))
        texts.append(ax.text(lon[mxy[i], mxx[i]], lat[mxy[i], mxx[i]], '\n' + str(data[mxy[i], mxx[i]].astype('int')),
                             color="gray", size=10, clip_on=True, fontweight='bold',
                             horizontalalignment='center', verticalalignment='top', zorder=6))
    return (texts)


def add_vals_on_map(ax, projection, var, levels, density=50,
                    cmap='rainbow', shift_x=0., shift_y=0., fontsize=8, lcolors=True):
    '''Given an input projection, a variable containing the values and a plot put
    the values on a map exlcuing NaNs and taking care of not going
    outside of the map boundaries, which can happen.
    - shift_x and shift_y apply a shifting offset to all text labels
    - colors indicate whether the colorscale cmap should be used to map the values of the array'''

    norm = colors.Normalize(vmin=levels.min(), vmax=levels.max())
    m = mplcm.ScalarMappable(norm=norm, cmap=cmap)

    proj_options = proj_defs[projection]
    lon_min, lon_max, lat_min, lat_max = proj_options['llcrnrlon'], proj_options['urcrnrlon'],\
        proj_options['llcrnrlat'], proj_options['urcrnrlat']

    # Remove values outside of the extents
    var = var.sel(lat=slice(lat_min + 0.15, lat_max - 0.15),
                  lon=slice(lon_min + 0.15, lon_max - 0.15))[::density, ::density]
    lons = var.lon
    lats = var.lat

    at = []
    for ilat, ilon in np.ndindex(var.shape):
        if lcolors:
            at.append(ax.annotate(('%d' % var[ilat, ilon]), (lons[ilon] + shift_x, lats[ilat] + shift_y),
                                  color=m.to_rgba(float(var[ilat, ilon])), weight='bold', fontsize=fontsize,
                                  path_effects=[path_effects.withStroke(linewidth=1, foreground="black")], zorder=5))
        else:
            at.append(ax.annotate(('%d' % var[ilat, ilon]), (lons[ilon] + shift_x, lats[ilat] + shift_y),
                                  color='white', weight='bold', fontsize=fontsize,
                                  path_effects=[path_effects.withStroke(linewidth=1, foreground="black")], zorder=5))

    return at


def compute_rate(dset):
    '''Given an accumulated variable compute the step rate'''
    try:
        rain_acc = dset['RAIN_GSP'] + dset['RAIN_CON']
    except:
        rain_acc = dset['RAIN_GSP']
    try:
        snow_acc = dset['lssrwe'] + dset['csrwe']
    except:
        snow_acc = dset['lssrwe']

    rain = rain_acc.differentiate(coord="step", datetime_unit="h")
    snow = snow_acc.differentiate(coord="step", datetime_unit="h")

    rain = xr.DataArray(rain, name='rain_rate')
    snow = xr.DataArray(snow, name='snow_rate')

    return xr.merge([dset, rain, snow])
