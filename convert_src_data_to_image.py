#!/usr/bin/env python

import json
import math
import matplotlib.cm as cm
import matplotlib.colors as colors
import matplotlib.image as mpimg
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import rasterio
import sys

from matplotlib.colors import LinearSegmentedColormap

LOCATIONS = json.load(open('locations.json', 'r'))

MIN_PRECIP = 0.0
MAX_PRECIP = 300.0

MIN_TMAX = 50.0
MAX_TMAX = 95.0

MIN_DEW_POINT = 50.0
MAX_DEW_POINT = 75.0

MONTH_DEGREES = 30


def temp_to_hue(temp, min_temp=MIN_TMAX, max_temp=MAX_TMAX):
    normalized_temp = (np.clip(temp, min_temp, max_temp) - min_temp) / (max_temp - min_temp)
    return 2/3 * (1 - normalized_temp)

def dew_point_to_alpha(dew_point_fahrenheit):
    return 1.0 - max([min([dew_point_fahrenheit - 50, 25]), 0]) / 25 * 0.9

def precip_to_width_fraction(precip, min_precip=MIN_PRECIP, max_precip=MAX_PRECIP):
    return 1 - (np.clip(precip, min_precip, max_precip) - min_precip) / (max_precip - min_precip) * .9

def temp_and_vapr_to_relative_humidity(temperature_fahrenheit, vapor_pressure):
    temperature_celsius = (temperature_fahrenheit - 32) * 5 / 9
    saturation_vapor_pressure = 0.6108 * math.exp((17.27 * temperature_celsius) / (temperature_celsius + 237.3))
    return 100 * vapor_pressure / saturation_vapor_pressure

def get_map_outline():
    src = rasterio.open('data/wc2.1_10m_prec_01.tif')
    data = src.read(1)
    outline = (data == -32768) * 0.5
    return outline

def calculate_dew_point(temperature_fahrenheit, relative_humidity):
    temperature_celsius = (temperature_fahrenheit - 32.0) * 5 / 9
    a = 17.27
    b = 237.7
    alpha = ((a * temperature_celsius) / (b + temperature_celsius)) + math.log(relative_humidity / 100.0)
    dew_point_celsius = (b * alpha) / (a - alpha)
    dew_point_fahrenheit = dew_point_celsius * 9 / 5  + 32.0
    return dew_point_fahrenheit


fig, ax = plt.subplots(figsize=(20, 7))

ax.imshow(get_map_outline(), cmap='gray', extent=[-180, 180, -90, 90])  # Adjust the extent as needed


for month in range(0, 12):
    radius = 2.5
    angle = (90 - month * MONTH_DEGREES) % 360

    month_str = f"{month+1:02d}"
    tmax_filename = f"data/wc2.1_10m_tmax_{month_str}.tif"
    precip_filename = f"data/wc2.1_10m_prec_{month_str}.tif"
    vapr_filename = f"data/wc2.1_10m_vapr_{month_str}.tif"

    tmax_src = rasterio.open(tmax_filename)
    precip_src = rasterio.open(precip_filename)
    vapr_src = rasterio.open(vapr_filename)

    tmax_data = tmax_src.read(1)
    tmax_data = tmax_data.clip(-1000, 1000) * 9.0 / 5.0 + 32

    precip_data = precip_src.read(1)
    vapr_data = vapr_src.read(1)

    assert tmax_data.shape == precip_data.shape, "Shapes do not match"

    for location in LOCATIONS:
        name, lat, lon = [location[key] for key in ['name', 'latitude', 'longitude']]

        transform = tmax_src.transform
        inverse_transform = ~transform

        px, py = map(int, inverse_transform * (lon, lat))
        tmax = tmax_data[py, px]
        precip = precip_data[py, px]
        vapr = vapr_data[py, px]

        relative_humidity = temp_and_vapr_to_relative_humidity(tmax, vapr)
        dew_point = calculate_dew_point(tmax, relative_humidity)

        hue = temp_to_hue(tmax)
        width_fraction = precip_to_width_fraction(precip)
        width = radius * width_fraction

        # month 0 = 90
        # month 1 = 60
        # month 2 = 30
        # month 3 = 0
        # month 4 = 330

        saturation = 1.0
        color = colors.hsv_to_rgb((hue, 1.0, 1.0))

        # 75 - should be 0.1
        # 50 - should be 1.0
        alpha = dew_point_to_alpha(dew_point)

        wedge = patches.Wedge(center=(lon, lat), r=radius, theta1=angle - MONTH_DEGREES, theta2=angle, color=color, width=width, alpha=alpha, linewidth=0.0)
        ax.add_patch(wedge)

        print(f"{name}\t{month+1}\t{tmax}\t{precip}\t{dew_point}")


# cmap_precip = LinearSegmentedColormap.from_list(
#     "my_colormap_precip",
#     [colors.hsv_to_rgb((temp_to_hue(25), precip_to_saturation(precip), 1)) for precip in np.linspace(MIN_PRECIP, MAX_PRECIP, num=256)]
# )
# 
# # Create a colorbar using this colormap
# cbar_precip = fig.colorbar(cm.ScalarMappable(norm=colors.Normalize(MIN_PRECIP, MAX_PRECIP), cmap=cmap_precip), ax=ax)
# cbar_precip.set_label('Precipitation (mm)')

# Coordinates for the custom legend
legend_x = 250  # Adjust as needed
legend_y_start = 80  # Adjust as needed
spacing = 10  # Vertical spacing between wedges

# Define a few representative precipitation values for the legend
precip_values = [MIN_PRECIP, 50, 100, 150, MAX_PRECIP]
precip_values = list(np.linspace(MIN_PRECIP, MAX_PRECIP, 7))

ax.set_xlim([-180, 300])  # Extend the x-axis limit
ax.set_ylim([-90, 100])   # Extend the y-axis limit if needed


# Draw the wedges for the custom legend
for i, precip in enumerate(precip_values):
    width_fraction = precip_to_width_fraction(precip)
    width = 2.5 * width_fraction  # Adjust size as needed
    wedge = patches.Wedge(center=(legend_x, legend_y_start - i * spacing), r=2.5, theta1=0, theta2=360, width=width, color='blue', linewidth=0.0)
    ax.add_patch(wedge)
    ax.text(legend_x + 3, legend_y_start - i * spacing, f'{precip} mm', verticalalignment='center')




cmap_tmax = LinearSegmentedColormap.from_list(
    "my_colormap",
    [colors.hsv_to_rgb((temp_to_hue(temp), 1, 1)) for temp in np.linspace(MIN_TMAX, MAX_TMAX, num=256)]
)
cbar_tmax = fig.colorbar(cm.ScalarMappable(norm=colors.Normalize(MIN_TMAX, MAX_TMAX), cmap=cmap_tmax), ax=ax)
cbar_tmax.set_label('Temperature (F)')

cmap_dew_point = LinearSegmentedColormap.from_list(
    "my_colormap_dew_point",
    [(0, 0, 1, dew_point_to_alpha(dew_point)) for dew_point in np.linspace(MIN_DEW_POINT, MAX_DEW_POINT, num=256)]
)
cbar_dew_point = fig.colorbar(cm.ScalarMappable(norm=colors.Normalize(MIN_DEW_POINT, MAX_DEW_POINT), cmap=cmap_dew_point), ax=ax)
cbar_dew_point.set_label('Dew Point (F)')


plt.savefig('monthly_climate_map.png', dpi=300)
