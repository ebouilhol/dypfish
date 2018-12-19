#!/usr/bin/python
# encoding: UTF-8

import numpy as np
from random import *
import h5py
import matplotlib.pyplot as plt
import src.path as path
import src.helpers as helps
import src.image_descriptors as idsc
from src.utils import enable_logger, check_dir
from numpy import mean, median, absolute

def mean_absolute_deviation(data, axis=None):
    return mean(absolute(data - mean(data, axis)), axis)

def median_absolute_deviation(data, axis=None):
    return median(absolute(data - median(data, axis)), axis)

def get_spots_peripheral_distance_2D(spots,nucleus_mask,cell_mask,periph_dist_map):
    spots_peripheral_distance_2D = []
    for spot in spots:
        if nucleus_mask[spot[1], spot[0]] == 0:
            if cell_mask[spot[1], spot[0]] == 1 and periph_dist_map[spot[1], spot[0]] == 0:
                spots_peripheral_distance_2D.append(int(1))
            else:
                spots_peripheral_distance_2D.append(periph_dist_map[spot[1], spot[0]])
    print(spots_peripheral_distance_2D)
    return np.array(spots_peripheral_distance_2D)

def main():
    # Required descriptors: cell_area (built from cell_mask), spots
    # Import basics descriptors in H5 Format using 'import_h5.sh' or use own local file
    # This import script takes username and password arguments to connect to remote server bb8
    enable_logger()

    ## Control reproducibility mrna distribution for arhgdia and arhgdia cultured
    with h5py.File(path.basic_file_path, "a") as file_handler, \
            h5py.File(path.secondary_file_path, "a") as sec_file_handler:
        check_dir(path.analysis_dir + "/analysis_stability/figures/")

        # Build all image for an acquisition
        arhgdia = helps.build_image_list_2(file_handler, 'mrna', "arhgdia",["3h"])
        arhgdia_cultured = helps.build_image_list_2(file_handler, 'mrna', "arhgdia_cultured",["3h"])
        spots_peripheral_distances = np.array([idsc.get_spots_peripheral_distance_2D(sec_file_handler, x) for x in arhgdia])
        total_mads_arhgdia = []
        peripheral_profiles=np.zeros((len(spots_peripheral_distances),10))
        for j in range(len(spots_peripheral_distances)):
            for i in range(0, 10):
                peripheral_profiles[j, i] = float(len(np.where((spots_peripheral_distances[j] >= ((i*10) + 1)) & (spots_peripheral_distances[j] <= (i + 1)*10))[0]) / float(len(spots_peripheral_distances[j])))
        for j in range(500):
            print(j)
            mads = []
            for i in range (1,40):
                arr=peripheral_profiles[np.random.choice(peripheral_profiles.shape[0], i, replace=True)]
                mean_arr = np.mean(arr, axis=0)
                rand_idx=randint(0, peripheral_profiles.shape[0] - 1)
                arr_diff=mean_arr-peripheral_profiles[rand_idx,:]
                mse = mean_absolute_deviation(arr_diff)
                mads.append(mse)
            total_mads_arhgdia.append(mads)
        spots_peripheral_distances = np.array([get_spots_peripheral_distance_2D(idsc.get_spots(file_handler, x),idsc.get_nucleus_mask(file_handler, x),idsc.get_cell_mask(file_handler, x),idsc.get_cell_mask_distance_map(sec_file_handler, x)) for x in arhgdia_cultured])
        total_mads_arhgdia_cultured = []
        peripheral_profiles = np.zeros((len(spots_peripheral_distances), 10))
        for j in range(len(spots_peripheral_distances)):
            for i in range(0, 10):
                peripheral_profiles[j, i] = float(len(np.where((spots_peripheral_distances[j] >= ((i * 10) + 1)) & (spots_peripheral_distances[j] <= (i + 1) * 10))[0]) / float(len(spots_peripheral_distances[j])))
        for j in range(500):
            print(j)
            mads = []
            for i in range(1, 24):
                arr = peripheral_profiles[np.random.choice(peripheral_profiles.shape[0], i, replace=True)]
                rand_idx=randint(0, peripheral_profiles.shape[0] - 1)
                mean_arr = np.mean(arr, axis=0)
                arr_diff = mean_arr - peripheral_profiles[rand_idx, :]
                mse = mean_absolute_deviation(arr_diff)
                mads.append(mse)
            total_mads_arhgdia_cultured.append(mads)

        plt.figure()
        ax = plt.axes()
        ax.tick_params(right=False, top=False, bottom=False, direction='inout', length=8, width=3, colors='black')
        for axis in ['left']:
            ax.spines[axis].set_linewidth(3)
        plt.yticks(fontsize=20)
        plt.xticks(fontsize=20)
        ax.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
        print(total_mads_arhgdia)
        plt.plot(np.mean(total_mads_arhgdia, axis=0),color='blue')
        plt.plot(np.mean(total_mads_arhgdia_cultured, axis=0),color='black')
        ax.set_xlim(0, 20)
        plt.savefig(path.analysis_dir + "/analysis_stability/figures/stability_analysis.png")
        plt.show()

if __name__ == "__main__":
    main()
