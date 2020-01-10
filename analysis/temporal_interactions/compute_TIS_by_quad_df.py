#!/usr/bin/python
# encoding: UTF-8
# author: benjamin Dartigues


import numpy as np
import h5py
import argparse
import math
import pandas as pd
import src.image_descriptors as idsc
import src.path as path
import src.helpers as helps
from src.utils import enable_logger, check_dir, loadconfig

parser = argparse.ArgumentParser()
parser.add_argument("--input_dir_name", "-i", help='input dir where to find h5 files and configuration file', type=str)
args = parser.parse_args()
input_dir_name = args.input_dir_name

def compute_eight_quadrant_max(file_handler, image, degree_max, image_width, image_height):
    print(image)
    mtoc_position = idsc.get_mtoc_position(file_handler, image)
    height_map = idsc.get_height_map(file_handler, image)
    nucleus_centroid = idsc.get_nucleus_centroid(file_handler, image)
    cell_mask = idsc.get_cell_mask(file_handler, image)
    nucleus_mask = idsc.get_nucleus_mask(file_handler, image)
    height_map = height_map.astype(float)
    height_map[cell_mask == 0] = 0
    height_map[nucleus_mask == 1] = 0

    # the quadrant of MTOC is defined by two lines 45 degrees to the right
    right_point = helps.rotate_point(nucleus_centroid, mtoc_position, int(degree_max))
    s = helps.slope_from_points(nucleus_centroid, right_point)
    corr = np.arctan(s)  # angle wrt to x axis
    xx, yy = np.meshgrid(np.array(range(0, image_width)) - nucleus_centroid[0], np.array(range(0, image_height)) - nucleus_centroid[1])
    rotated_xx, rotated_yy = helps.rotate_meshgrid(xx, yy, -corr)
    sliceno = ((math.pi + np.arctan2(rotated_xx, rotated_yy)) * (4 / (math.pi)))
    sliceno = sliceno.astype(int)
    quadrant_mask = sliceno + cell_mask
    quadrant_mask[quadrant_mask == 9] = 8
    quadrant_mask[cell_mask == 0] = 0
    mtoc_quad = quadrant_mask[mtoc_position[1], mtoc_position[0]]

    return quadrant_mask, mtoc_quad

def compute_four_quadrant_max(file_handler, image, degree_max, image_width, image_height):
    print(image)
    mtoc_position = idsc.get_mtoc_position(file_handler, image)
    height_map = idsc.get_height_map(file_handler, image)
    nucleus_centroid = idsc.get_nucleus_centroid(file_handler, image)
    cell_mask = idsc.get_cell_mask(file_handler, image)
    nucleus_mask = idsc.get_nucleus_mask(file_handler, image)
    height_map = height_map.astype(float)
    height_map[cell_mask == 0] = 0
    height_map[nucleus_mask == 1] = 0

    # the quadrant of MTOC is defined by two lines 45 degrees to the right
    right_point = helps.rotate_point(nucleus_centroid, mtoc_position, int(degree_max)-1)
    s = helps.slope_from_points(nucleus_centroid, right_point)
    corr = np.arctan(s)  # angle wrt to x axis
    xx, yy = np.meshgrid(np.array(range(0, image_width)) - nucleus_centroid[0], np.array(range(0, image_height)) - nucleus_centroid[1])
    rotated_xx, rotated_yy = helps.rotate_meshgrid(xx, yy, -corr)
    sliceno = ((math.pi + np.arctan2(rotated_xx, rotated_yy)) * (4 / (2 * math.pi)))
    sliceno = sliceno.astype(int)
    quadrant_mask = sliceno + cell_mask
    quadrant_mask[quadrant_mask == 5] = 4
    quadrant_mask[cell_mask == 0] = 0
    mtoc_quad = quadrant_mask[mtoc_position[1], mtoc_position[0]]

    return quadrant_mask, mtoc_quad


def map_index(x,mtoc_quad):
    print(mtoc_quad)
    if x >= mtoc_quad:
        new_index=(x-mtoc_quad+1)
    else:
        new_index=(x+8-mtoc_quad+1)
    return new_index

def reindex_eight_quadrant_mask(quad_mask, mtoc_quad):
     df=pd.DataFrame(quad_mask)
     df=df.applymap(lambda x: x - mtoc_quad + 1 if x >= mtoc_quad else (x + 8 - mtoc_quad + 1 if x > 0 else 0))
     quad_mask=np.array(df)
     return quad_mask

def reindex_four_quadrant_mask(quad_mask, mtoc_quad):
    df = pd.DataFrame(quad_mask)
    df = df.applymap(lambda x: x - mtoc_quad + 1 if x >= mtoc_quad else (x + 4 - mtoc_quad + 1 if x > 0 else 0))
    quad_mask = np.array(df)
    return quad_mask

def compute_TIS(configData, degree_max_mrna, degree_max_protein, number_of_quadrants):
    mrnas = configData["GENES"][0:4]
    proteins = configData["PROTEINS"]
    timepoints_mrna = configData["TIMEPOINTS_MRNA"]
    timepoints_protein = configData["TIMEPOINTS_PROTEIN"]
    stripe_n = configData["STRIPE_NUM"]
    size_coeff = configData["SIZE_COEFFICIENT"]
    basic_file_name = configData["BASIC_FILE_NAME"]
    secondary_file_name = configData["SECONDARY_FILE_NAME"]
    image_width=configData["IMAGE_WIDTH"]
    image_height = configData["IMAGE_HEIGHT"]

    # Compute global TIS
    with h5py.File(path.data_dir + input_dir_name + '/' + basic_file_name, "r") as file_handler, \
            h5py.File(path.data_dir + input_dir_name + '/' + secondary_file_name, "r") as second_file_handler:
        gene_count = 0
        for mrna in mrnas:
            time_count = 0
            for timepoint in timepoints_mrna:
                key = mrna + "_" + timepoint
                image_count = 0
                h_array = np.zeros((len(degree_max_mrna[key]), stripe_n * number_of_quadrants))
                for i in range(len(degree_max_mrna[key])):
                    image = degree_max_mrna[key][i].split("_")[0]
                    degree = degree_max_mrna[key][i].split("_")[1]
                    image = "/mrna/" + mrna + "/" + timepoint + "/" + image
                    if number_of_quad==8:
                        quad_mask, mtoc_quad = compute_eight_quadrant_max(file_handler, image, degree, image_width, image_height)
                        quad_mask = reindex_eight_quadrant_mask(quad_mask, mtoc_quad)
                    else:
                        quad_mask, mtoc_quad = compute_four_quadrant_max(file_handler, image, degree, image_width,image_height)
                        quad_mask = reindex_four_quadrant_mask(quad_mask, mtoc_quad)


                    nucleus_mask = idsc.get_nucleus_mask(file_handler, image)
                    cell_mask = idsc.get_cell_mask(file_handler, image)
                    spots = idsc.get_spots(file_handler, image)
                    cell_mask_dist_map = idsc.get_cell_mask_distance_map(second_file_handler, image)
                    cell_mask_dist_map[(cell_mask == 1) & (cell_mask_dist_map == 0)] = 1
                    cell_mask_dist_map[(nucleus_mask == 1)] = 0

                    for i in range(len(spots)):
                        if idsc.is_in_cytoplasm(file_handler, image, [spots[i, 1], spots[i, 0]]):
                            quad = quad_mask[spots[i, 1], spots[i, 0]]
                            value = cell_mask_dist_map[spots[i, 1], spots[i, 0]]
                            if value == 100:
                                value = 99
                            dist = value
                            slice_area = np.floor(value / (100.0 / stripe_n))
                            value = (int(slice_area) * number_of_quadrants) + int(quad - 1)
                            h_array[image_count, int(value)] += (1.0 / len(spots)) / float(
                                np.sum(cell_mask[(cell_mask_dist_map == dist) & (quad_mask == quad)]) * math.pow(
                                    (1 / size_coeff), 2))
                    image_count += 1
                mrna_tp_df = pd.DataFrame(h_array)
                mrna_tp_df.to_csv(check_dir(path.analysis_dir + "temporal_interactions/dataframe/") +
                                  mrna + '_' + timepoint + "_mrna.csv")
                time_count += 1
            gene_count += 1
        gene_count = 0
        for protein in proteins:
            time_count = 0
            for timepoint in timepoints_protein:
                key = protein + "_" + timepoint
                image_count = 0
                h_array = np.zeros((len(degree_max_protein[key]), number_of_quadrants * stripe_n))
                for i in range(len(degree_max_protein[key])):
                    image = degree_max_protein[key][i].split("_")[0]
                    degree = degree_max_protein[key][i].split("_")[1]
                    image = "/protein/" + protein + "/" + timepoint + "/" + image

                    if number_of_quad == 8:
                        quad_mask, mtoc_quad = compute_eight_quadrant_max(file_handler, image, degree, image_width,image_height)
                        quad_mask = reindex_eight_quadrant_mask(quad_mask, mtoc_quad)
                    else:
                        quad_mask, mtoc_quad = compute_four_quadrant_max(file_handler, image, degree, image_width,image_height)
                        quad_mask = reindex_four_quadrant_mask(quad_mask, mtoc_quad)

                    cell_mask = idsc.get_cell_mask(file_handler, image)
                    nucleus_mask = idsc.get_nucleus_mask(file_handler, image)
                    cell_mask_dist_map = idsc.get_cell_mask_distance_map(second_file_handler, image)
                    IF = idsc.get_IF(file_handler, image)
                    count = 0
                    IF[(cell_mask == 0)] = 0
                    IF[(nucleus_mask == 1)] = 0
                    cell_mask_dist_map[(cell_mask == 1) & (cell_mask_dist_map == 0)] = 1
                    for i in range(1, 99):
                        for j in range(1, number_of_quadrants+1):
                            value = int(np.floor(i / (100.0 / stripe_n)))
                            value = (int(value) * number_of_quadrants) + int(j - 1)
                            if np.sum(cell_mask[(cell_mask_dist_map == i) & (quad_mask == j)]) == 0:
                                h_array[image_count, value] = 0.0
                            else:
                                h_array[image_count, value] = (float(
                                    np.sum(IF[(cell_mask_dist_map == i) & (quad_mask == j)])) / float(
                                    np.sum(IF))) / np.sum(cell_mask[(cell_mask_dist_map == i) & (quad_mask == j)])
                        count += 1
                    image_count += 1
                prot_tp_df = pd.DataFrame(h_array)
                prot_tp_df.to_csv(
                    path.analysis_dir + "temporal_interactions/dataframe/" + protein + '_' + timepoint + "_protein.csv")
                time_count += 1
            gene_count += 1


def main():
    enable_logger()
    configData = loadconfig(input_dir_name)

    try:
        df = pd.read_csv(check_dir(path.analysis_dir + 'MTOC/dataframe/') + 'global_mtoc_file_mrna.csv')
    except IOError:
        print "Couldn't load file : ", path.analysis_dir + 'MTOC/dataframe/' + 'global_mtoc_file_mrna.csv'
        print "Maybe MTOC analysis hasn't been launched for mRNA prior to this one"
        exit(1)
    df_sorted = df.sort_values('MTOC', ascending=False).groupby(['Gene', 'timepoint', 'Image'],as_index=False).first()
    degree_max_mrna = {}
    for gene, line in df_sorted.groupby(['Gene', 'timepoint']):
        key = gene[0] + "_" + gene[1]
        degree_max_mrna[key] = line['Unnamed: 0'].values

    try:
        df = pd.read_csv(check_dir(path.analysis_dir + 'MTOC/dataframe/') + 'global_mtoc_file_protein.csv')
    except IOError:
        print "Couldn't load file : ", path.analysis_dir + 'MTOC/dataframe/' + 'global_mtoc_file_protein.csv'
        print "Maybe MTOC analysis hasn't been launched for protein prior to this one"
        exit(1)
    df_sorted = df.sort_values('MTOC', ascending=False).groupby(['Gene', 'timepoint', 'Image'], as_index=False).first()
    degree_max_protein = {}
    for gene, line in df_sorted.groupby(['Gene', 'timepoint']):
        key = gene[0] + "_" + gene[1]
        degree_max_protein[key] = line['Unnamed: 0'].values

    compute_TIS(configData, degree_max_mrna, degree_max_protein, number_of_quad=8)

if __name__ == "__main__":
    main()