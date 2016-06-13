#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

import argparse
import gdal
import h5py
import math
import matplotlib.pyplot as plt
import numpy as np
import scipy.misc as im
import sys

"""
    Module: All the program of viewing land
"""


#################################################
def hillshade(array, azimuth, angle_altitude):
    """
        Compute the display by an angle.
            - Come from http://geoexamples.blogspot.ch/2014/03/shaded-relief-images-using-gdal-python.html
        Written by Roger Veciana i Rovira.

        @param array: all the numeric values of the land
        @param azimuth:
        @param angle_altitude:the angle of view
    """
    x, y = np.gradient(array)
    slope = np.pi / 2. - np.arctan(np.sqrt(x * x + y * y))
    aspect = np.arctan2(-x, y)
    azimuthrad = azimuth * np.pi / 180.
    altituderad = angle_altitude * np.pi / 180.

    shaded = np.sin(altituderad) * np.sin(slope) + np.cos(altituderad) * np.cos(slope) * np.cos(azimuthrad - aspect)
    return 255 * (shaded + 1) / 2


#################################################
def parsing():
    """
        Parse all the argument using the "py" lib : argparse.

        @return returned_values: a dictionnary with all important value used in this programm
    """

    # we have this arguments for futur ploting with default value
    img_path = None
    center_x = None
    center_y = None
    width = None
    height = None
    render = 'gist_earth'
    angle = 150
    cender_path = None
    alpha = 1

    # define the arguments using argparse
    parser = argparse.ArgumentParser()

    # this is all the argument, with the help
    parser.add_argument("--img", dest="filepath", help="Filepath to the image")
    parser.add_argument("--posx", dest="posx", help="Define the position x of the volcan. MUST BE USED WITH posy")
    parser.add_argument("--posy", dest="posy", help="Define the position y of the volcan. MUST BE USED WITH posx")
    parser.add_argument("--width", dest="width", help="Define the width scaling. MUST BE USED WITH height")
    parser.add_argument("--height", dest="height", help="Define the height scaling.MUST BE USED WITH width")
    parser.add_argument("--render", dest="render", help="Define the render type. Gist_earth by default")
    parser.add_argument("--angle", dest="angle", help="Define the angle of viewing. By default to 150°")
    parser.add_argument("--ash", dest="ash", help="Define the ash's filepath. MUST BE USED WITH posx AND posy")
    parser.add_argument("--alpha", dest="alpha", help="Define the opacity of the render")

    # we parse it
    args = parser.parse_args()
    # then put it in the programme
    if args.filepath:
        img_path = args.filepath
    if args.posx:
        center_x = args.posx
    if args.posy:
        center_y = args.posy
    if args.width:
        width = args.width
    if args.height:
        height = args.height
    if args.render:
        render = args.render
    if args.angle:
        angle = args.angle
    if args.ash:
        cender_path = args.ash
    if args.alpha:
        alpha = args.alpha

    # we keep the value in a dictionnary to give back
    returned_values = {}
    returned_values["img"] = gdal.Open(img_path)
    returned_values["center_x"] = (center_x if center_x is None else float(center_x))
    returned_values["center_y"] = (center_y if center_y is None else float(center_y))
    returned_values["width"] = (width if width is None else int(width))
    returned_values["height"] = (height if height is None else int(height))
    returned_values["render"] = render
    returned_values["angle"] = float(angle)
    returned_values["cender_path"] = cender_path
    returned_values["alpha_land"] = float(alpha)

    return returned_values


#################################################
def convert_information(returned_values):
    """
        Here, we converte the distance from km to degree.

        @param returned_values: the dictionnary containing all varabile
        @return dictionnary with all updated value
    """

    # we take all the information for converting the latitude to longitude
    width_x = returned_values["img"].RasterXSize
    height_y = returned_values["img"].RasterYSize
    geo_t = returned_values["img"].GetGeoTransform()
    minx = geo_t[0]
    miny = geo_t[3] + width_x * geo_t[4] + height_y * geo_t[5]
    maxx = geo_t[0] + width_x * geo_t[1] + height_y * geo_t[2]
    maxy = geo_t[3]

    # we have coordinate in long,lat, so we don't need to change them
    # we change the width and the heigth from km to long,lat if it exists
    lat_height = None
    long_width = None
    if (returned_values["height"] is not None and returned_values["width"] is not None):
        lat_height = (returned_values["height"] / 110.574)
        long_width = (returned_values["width"] / (111.320 * math.cos(lat_height * 0.01745)))
        lat_height = (abs(maxy - miny) if lat_height > abs(maxy - miny) else lat_height)
        long_width = (abs(maxx - minx) if long_width > abs(maxx - minx) else long_width)

    # we want to know the distance in degree between two element of the matrix
    step_x = abs(maxx - minx) / width_x
    step_y = abs(maxy - miny) / height_y

    # we store all that in the dictionnary to use later
    returned_values["width_x"] = width_x
    returned_values["height_y"] = height_y
    returned_values["minx_d"] = minx
    returned_values["maxx_d"] = maxx
    returned_values["miny_d"] = miny
    returned_values["maxy_d"] = maxy
    returned_values["lat_height"] = lat_height
    returned_values["long_width"] = long_width
    returned_values["step_x"] = step_x
    returned_values["step_y"] = step_y

    # we do the manipulation with the coordinate only if they aren't None
    if (returned_values["center_x"] is not None and returned_values["center_y"] is not None):
        # just checked if the coordinate aren't outside of image
        if (float(returned_values["center_x"]) > maxx or float(returned_values["center_x"]) < minx or float(returned_values["center_y"]) < miny or float(returned_values["center_y"]) > maxy):

            print "Min & Max Value\nmin x = ", minx, " , max x = ", maxx, " min y = ", miny, " max y = ", maxy

            # define center point if the previous point was outside
            returned_values["center_x"] = (minx + maxx) / 2
            returned_values["center_y"] = (miny + maxy) / 2

    return returned_values


#################################################
def lat_long_2_x_y(lng, lat, returned_values):
    """
    Change the referential of a point with a simple cross-product.
    @param lat : latitude value of new point
    @param lng : longitude value of new point
    @param returned_values : give us the minimal value for lat/long of image and the steps

    @return A list including the new coordinates.
    """
    y = abs(lat - returned_values["maxy_d"]) / returned_values["step_y"]
    x = abs(lng - returned_values["minx_d"]) / returned_values["step_x"]
    return [x, y]


#################################################
def rescale_matrix(elevation, returned_values):
    """
        Take a matrix, and resize it with correct width and heigth

        @param elevation: matrix to resize

        @param returned_values: contains all important variables

        @return [elevation,returned_values]: the rescale elevation and the updated values in dictionnary
    """
    # we take the width and height in long/lat
    width = returned_values["long_width"]
    height = returned_values["lat_height"]
    # we converte the point [x,y] at each corner of the grid
    x_0, y_0 = lat_long_2_x_y(returned_values["center_x"] - width / 2, returned_values["center_y"] - height / 2, returned_values)
    x_1, y_1 = lat_long_2_x_y(returned_values["center_x"] + width / 2, returned_values["center_y"] + height / 2, returned_values)

    # we check for the problem case
    x_0 = (0 if x_0 < 0 else x_0)

    x_0 = (returned_values["width_x"] if x_0 > returned_values["width_x"] else x_0)

    y_0 = (returned_values["height_y"] if y_0 > returned_values["height_y"] else y_0)

    y_0 = (0 if y_0 < 0 else y_0)

    x_1 = (returned_values["width_x"] if x_1 > returned_values["width_x"] else x_1)

    x_1 = (0 if x_1 < 0 else x_1)

    y_1 = (returned_values["height_y"] if y_1 > returned_values["height_y"] else y_1)

    y_1 = (0 if y_1 < 0 else y_1)

    # we swap if it's necessary
    if x_0 > x_1:
        (x_0, x_1) = (x_1, x_0)
    if y_0 > y_1:
        (y_0, y_1) = (y_1, y_0)

    # reshape elevation
    # here the x and the y are interveted because the image has the information in the other way
    elevation = elevation[int(y_0):int(y_1), int(x_0):int(x_1)]

    # we change the referential of [x,y]
    returned_values["center_x_matrix"] = returned_values["center_x_matrix"] - int(x_0)
    returned_values["center_y_matrix"] = returned_values["center_y_matrix"] - int(y_0)

    return [elevation, returned_values]


#################################################
def display_land_without_ash(returned_values):
    """
        This function display the land, with some possible option.
        We can add a point, and/or scale the imagei.

            1. Display point if it exist
            2. Scale if it exist
            3. Plot the image

        @param returned_values: dictionnary with all value
    """
    # begining of the ploting graph's algorithm
    bs = returned_values["img"]
    band = bs.GetRasterBand(1)
    elevation = band.ReadAsArray()

    # we run the updating information function
    returned_values = convert_information(returned_values)

    # if the [x,y] aren't Nonve value, the we plot them
    if (returned_values["center_x"] is not None and returned_values["center_y"] is not None):
        [returned_values["center_x_matrix"], returned_values["center_y_matrix"]] = lat_long_2_x_y(returned_values["center_x"], returned_values["center_y"], returned_values)

        # test if we need to scale of not
        if (returned_values["width"] is not None and returned_values["height"] is not None):
            [elevation, returned_values] = rescale_matrix(elevation, returned_values)

        # we plot the point
        # we change the starting point of y
        plt.plot(returned_values["center_x_matrix"], returned_values["center_y_matrix"], 'ro')

    # update the elevation for relief
    elevation = hillshade(elevation, 0, returned_values["angle"])
    ax = plt.gca()
    ax.axes.get_yaxis().set_visible(False)
    ax.axes.get_xaxis().set_visible(False)

    plt.imshow(elevation, cmap=returned_values["render"], alpha=returned_values["alpha_land"])

    plt.show()


#################################################
def load_cender(returned_values):
    """
        This function load the ash, take information about the center.
        And return a matrix with the ash level

        @param returned_values: give us the ash file path
        @return [center_point,matrix]: the point of volcan's center and the matrix of ash
    """
    # we load the file, get the attribut ,take the terrain_position, and the dx
    ash = h5py.File(returned_values["cender_path"])
    terrain_position = np.array(ash.attrs.get('terrain_position'))
    simulation_dx = np.array(ash.attrs.get('simulation_dx'))[0]

    # this is the key to acces of each "dimension" of ash
    list_key = ash.keys()

    # we create the matrix with a certain size
    matrix = np.array(ash.get(list_key.pop()))

    # we load ALL the ash
    for e1 in list_key:
        matrix += np.array(ash.get(e1))

    center_point = [abs(terrain_position[0] / simulation_dx), abs(terrain_position[1] / simulation_dx)]

    return [center_point, matrix, simulation_dx]


#################################################
def display_land_with_ash(returned_values):
    """
        Here we load the cender in a matrix, get the land matrix equivalent,
        and plot all of that together.

        @param returned_values: give us the ash_path, and the point and the elevation...
    """

    # first we load the cender
    [center_point, ash_matrix, dx] = load_cender(returned_values)

    # we load the elevation
    bs = returned_values["img"]
    band = bs.GetRasterBand(1)
    elevation = band.ReadAsArray()

    # we need to convert information
    returned_values = convert_information(returned_values)

    # we try to find the point x0,y0
    y_0 = returned_values["center_y"] - (center_point[1] / 111.574)
    x_0 = returned_values["center_x"] - (center_point[0] / (111.320 * math.cos((center_point[0] / 111.574) * 0.01745)))

    # we change the referential of points
    [x_0, y_0] = lat_long_2_x_y(x_0, y_0, returned_values)

    # we can transpose it, if it's necessary
    ash_matrix = np.transpose(ash_matrix)

    # i change the distance x and y of the cender as degree and i use that to know the number of element if the matrix
    x_ash = ash_matrix[0, :].size
    y_ash = ash_matrix[:, 0].size
    # convert it the degree
    y_degree = y_ash / 111.574
    x_degree = x_ash / (111.320 * math.cos(y_degree * 0.01745))

    # number of element
    x_number = x_degree / returned_values["step_x"]
    y_number = y_degree / returned_values["step_y"]

    # x and y are interveted for the same reason that sooner: not the same axis
    elevation = hillshade(elevation[int(y_0 - y_number):int(y_0), int(x_0):int(x_0 + x_number)], 0, returned_values["angle"])

    # we inverted the x_min and the x_max for ploting
    elevation = np.transpose(np.fliplr(np.transpose(elevation)))

    # we need to interpolate the ash_matrix to have the same size as the elevation
    ash_matrix = im.imresize(ash_matrix, elevation.shape, 'cubic')
    # we change the matrix for float
    ash_matrix = ash_matrix.astype(float)
    # we put the 0 value to nan for displaying
    ash_matrix[ash_matrix == 0.0] = np.nan

    plt.hold(True)
    plt.imshow(elevation, cmap=returned_values["render"])
    # then we plot it
    plt.imshow(ash_matrix, cmap="spectral", alpha=returned_values["alpha_land"])

    # small modification of axes
    plt.xlim(0, len(elevation[0, :]))
    plt.ylim(0, len(elevation[:, 0]))
    ax = plt.gca()
    ax.axes.get_yaxis().set_visible(False)
    ax.axes.get_xaxis().set_visible(False)

    # we plot the point
    plt.plot(int(center_point[0] * len(elevation[0, :]) / x_ash), int(center_point[1] * len(elevation[:, 0]) / y_ash), 'ro')
    plt.show()


#################################################
def main():
    """
        Main function. Call all the other function for:

            1. Parse te arguments
            2. Update returned_values.
            3. Display the land

    """

    # we parse the argument list with the function parsing()
    # but only if there is at lest one parameter
    if (len(sys.argv) <= 1):
        return
    returned_values = parsing()
    if returned_values["cender_path"] is None:
        display_land_without_ash(returned_values)
    else:
        display_land_with_ash(returned_values)


#################################################
# automaticaly start main when runing program
if __name__ == "__main__":
    main()
