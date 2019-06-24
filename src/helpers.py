from __future__ import print_function

import hashlib
import warnings
import os
import pandas
warnings.filterwarnings("ignore",category =RuntimeWarning)
import math
import h5py
import matplotlib.pyplot as plt
import numpy as np
from numpy import matlib
from scipy import signal
from skimage import draw
from skimage import measure
from skimage import io
import path
import constants
from logger import *

logger = logging.getLogger('DYPFISH_HELPERS')

def copy_dataset_and_attributes(input_path, output_path, datasets, attributes):
    input_file = h5py.File(input_path, 'a')
    for mol_type in input_file:
        print(mol_type)
        for mol_name in input_file[mol_type]:
            print(mol_name)
            for timepoint in input_file[mol_type + '/' + mol_name]:
                for image in input_file[mol_type + '/' + mol_name + '/' + timepoint]:
                    image_path = mol_type + '/' + mol_name + '/' + timepoint + '/' + image
                    print(image_path)
                    for dataset in datasets:
                        if dataset in input_file[image_path].keys():
                            old_path = mol_type + '/' + mol_name + '/' + timepoint + '/' + image + '/' + dataset
                            new_path = mol_type + '/' + mol_name + '/' + timepoint + '/' + image + '/' + dataset
                            command = '/home/ben/Bureau/hdf5-1.8.18/tools/h5copy/h5copy -p -i ' + input_path + ' -o ' + output_path + ' -s ' + old_path + ' -d ' + new_path
                            os.system(command)
                    for attribute in attributes:
                        if attribute in input_file['/' + image_path].attrs.keys():
                            old_path = mol_type + '/' + mol_name + '/' + timepoint + '/' + image + '/' + attribute
                            new_path = mol_type + '/' + mol_name + '/' + timepoint + '/' + image + '/' + attribute
                            command = '/home/ben/Bureau/hdf5-1.8.18/tools/h5copy/h5copy -p -i ' + input_path + ' -o ' + output_path + ' -s ' + old_path + ' -d ' + new_path
                            os.system(command)
    input_file.close()


def create_mask(row_coordinates, column_coordinates, image_shape):
    rr, cc = draw.polygon(row_coordinates, column_coordinates, shape=image_shape)
    mask = np.zeros(image_shape, dtype=np.bool)
    mask[rr, cc] = True
    return mask

def get_quantized_grid(q, Q):
    tmp = np.matrix(np.arange(Q))
    qxs = matlib.repmat(tmp.transpose(), 1, Q)
    qys = matlib.repmat(tmp, Q, 1)
    qxs = np.kron(qxs, np.ones((q, q)))
    print(qxs)
    plt.imshow(qxs)
    plt.show()
    qys = np.kron(qys, np.ones((q, q)))
    return qxs, qys


def get_IF_image_z_summed(molecule, gene, timepoint, image_number,path_data):
    if 'scratch' in path_data:
        IF_image_path = path_data +'/'+ molecule  + '/' + gene + timepoint + '/' + image_number.split('_')[0]+'_'+image_number.split('_')[1] + '/IF.tif'
    elif 'supp_data' in path_data:
        IF_image_path = path_data +'/'+ molecule  + '/' + gene + '/' + timepoint + '/' + image_number + '/IF.tif'
    else:
        IF_image_path = path_data +'/'+ molecule  + '/' + gene + '_' + timepoint + '/image_' + image_number + '/IF.tif'
    print(IF_image_path)
    IF = io.imread(IF_image_path, plugin='tifffile')
    IF = np.sum(IF, axis=0)
    return IF


def get_IF_image(molecule, type, timepoint, image_number,path_data):
    if 'scratch' in path_data:
        IF_image_path = path_data +'/'+ molecule  + '/' + type + timepoint + '/' + image_number.split('_')[0]+'_'+image_number.split('_')[1] + '/IF.tif'
    else:
        IF_image_path = path_data +'/'+ molecule  + '/' + type + '_' + timepoint + '/image_' + image_number + '/IF.tif'
    IF = io.imread(IF_image_path, plugin='tifffile')
    return IF


def save_plot_mask_spots_mrna(cell_mask, nucleus_mask, mtoc_position, nucleus_centroid, spots, csv_path):
    xs = spots[:, 0]
    ys = spots[:, 1]
    fig = plt.figure(figsize=(5, 5))
    plt.scatter(xs, ys, color='blue', marker="o", facecolors='none', linewidths=0.5)
    plt.imshow(cell_mask, cmap='gray')
    contours = measure.find_contours(nucleus_mask, 0.8)
    for n, contour in enumerate(contours):
        plt.plot(contour[:, 1], contour[:, 0], color='red', linewidth=2)
    img_path = csv_path.split("saveDetections_noforce_8080/FISH.tif.csv")[0]
    img_path = img_path + 'new_mask.png'
    plt.xticks([])
    plt.yticks([])
    plt.savefig(img_path)
    plt.close()


def save_plot_mask_spots_protein(cell_mask, nucleus_mask, mtoc_position, nucleus_centroid,image_dir):


    fig = plt.figure(figsize=(5, 5))
    plt.imshow(cell_mask, cmap='gray')
    contours = measure.find_contours(nucleus_mask, 0.8)
    plt.scatter(mtoc_position[0], mtoc_position[1], color='green', marker="d", linewidths=3)
    plt.scatter(nucleus_centroid[0], nucleus_centroid[1], color='black', marker="x", linewidths=3)
    for n, contour in enumerate(contours):
        plt.plot(contour[:, 1], contour[:, 0], color='blue', linewidth=2)

    img_path = image_dir + 'new_mask.png'
    plt.xticks([])
    plt.yticks([])
    plt.savefig(img_path)
    plt.close()


def plot_mask_and_spots(cell_mask, nucleus_mask, mtoc_position, nucleus_centroid, spots):
    xs = spots[:, 0]
    ys = spots[:, 1]
    plt.imshow(cell_mask, cmap='gray')
    # Find contours at a constant value of 0.8
    contours = measure.find_contours(nucleus_mask, 0.8)
    for n, contour in enumerate(contours):
        plt.plot(contour[:, 1], contour[:, 0], color='red', linewidth=2)
    plt.scatter(xs, ys, color='blue', marker="o", facecolors='none', linewidths=0.5)

def plot_mask(mask):
    plt.imshow(mask, cmap='gray')
    plt.show()

def build_quadrant_mask(index):
    quad_mask = np.zeros((512, 512))
    end = 511
    for i in range(256):
        if index == 1:
            quad_mask[i, i + 1:end - i + 1] = 1
        elif index == 2:
            quad_mask[i + 1:end - i + 1, end - i] = 1
        elif index == 3:
            quad_mask[end - i, i:end - i] = 1
        else:
            quad_mask[i:end - i, i] = 1
    return quad_mask


def check_presence(h5_file, image_path, datasets, attributes):
    all_found = True
    for key in datasets:
        if key not in h5_file[image_path].keys():
            all_found = False
    for key in attributes:
        if key not in h5_file[image_path].attrs.keys():
            all_found = False
    return all_found


def check_absence(h5_file, image_path, datasets, attributes):
    not_found = True
    for key in datasets:
        if key in h5_file[image_path].keys():
            not_found = False
    for key in attributes:
        if key in h5_file[image_path].attrs.keys():
            not_found = False
    return not_found


# build path from preliminary h5 files with basic descriptors
# need to be changed later to parse files system and find tif files later
def build_gene_and_spots_image_path(h5_file, molecule_type, raw_data_dir):
    image_path_list = []
    spots_file_path = []
    for gene_name in h5_file[molecule_type]:
        for timepoint in h5_file[molecule_type + '/' + gene_name]:
            for image in h5_file[molecule_type + '/' + gene_name + '/' + timepoint]:
                image_path = molecule_type + '/' + gene_name + '/' + timepoint + '/' + image
                image_path_list.append(image_path)
                spots_file = raw_data_dir + gene_name + '/mrna_' + timepoint + '/image_' + image + '/saveDetections_noforce_8080/FISH.tif.csv'
                spots_file_path.append(spots_file)
    return image_path_list, spots_file_path

# build an image list using molecule type and gene name
def build_image_list(file_handler, molecule, gene):
    image_list = []
    for timepoint in file_handler[molecule + '/' + gene]:
        for i in file_handler[molecule + '/' + gene + '/' + timepoint]:
            image = molecule + '/' + gene + '/' + timepoint + '/' + i
            image_list.append(image)
    return image_list

# build an image list using molecule type and gene name and timepoint
def build_image_list_2(file_handler, molecule, gene, timepoints):
    image_list = []
    for timepoint in timepoints:
        for i in file_handler[molecule + '/' + gene + '/' + timepoint]:
            image = molecule + '/' + gene + '/' + timepoint + '/' + i
            image_list.append(image)
    return image_list

def count_nucleus(file_handler, image):
    count = 0
    for dataset in file_handler[image]:
        if "nucleus_centroid" in dataset:
            count += 1
    if count == 0:
        count = 1
    return count

def preprocess_image(file_handler):
    """build path from preliminar h5 files with basic descriptors"""
    image_path_list = []
    for molecule in file_handler:
        for gene_name in file_handler[molecule]:
            for timepoint in file_handler[molecule + '/' + gene_name]:
                for image in file_handler[molecule + '/' + gene_name + '/' + timepoint]:
                    image_path = molecule + '/' + gene_name + '/' + timepoint + '/' + image
                    image_path_list.append(image_path)
    return image_path_list


def preprocess_image_list(file_handler, molecule_type):
    """build path from preliminar h5 files with basic descriptors"""
    image_path_list = []
    for molecule in molecule_type:
        print (file_handler.keys(),molecule)
        for gene_name in file_handler[molecule]:
            for timepoint in file_handler[molecule + '/' + gene_name]:
                for image in file_handler[molecule + '/' + gene_name + '/' + timepoint]:
                    image_path = molecule + '/' + gene_name + '/' + timepoint + '/' + image
                    image_path_list.append(image_path)
    return image_path_list


def preprocess_image_list2(file_handler, molecule,gene_name):
    """build path from preliminar h5 files with basic descriptors"""
    image_path_list = []
    for timepoint in file_handler[molecule + '/' + gene_name]:
        for image in file_handler[molecule + '/' + gene_name + '/' + timepoint]:
            image_path = molecule + '/' + gene_name + '/' + timepoint + '/' + image
            image_path_list.append(image_path)
    return image_path_list

def preprocess_image_list3(file_handler, molecule_type, gene, timepoints):
    """build path from preliminar h5 files with basic descriptors"""
    image_path_list = []
    for molecule in molecule_type:
        for timepoint in timepoints:
            node = molecule + '/' + gene + '/' + timepoint
            if node in file_handler.keys():
                for image in file_handler[node]:
                    image_path = molecule + '/' + gene + '/' + timepoint + '/' + image
                    image_path_list.append(image_path)
    return image_path_list


def preprocess_image_list4(file_handler, molecule_type, gene, timepoints,image_t):
    """build path from preliminar h5 files with basic descriptors"""
    image_path_list = []
    for molecule in molecule_type:
        for timepoint in timepoints:
            for image in file_handler[molecule + '/' + gene + '/' + timepoint]:
                if image_t in image:
                    image_path = molecule + '/' + gene + '/' + timepoint + '/' + image
                    image_path_list.append(image_path)
    return image_path_list


def preprocess_image_list5(file_handler, molecule,gene_name,image_t):
    """build path from preliminar h5 files with basic descriptors"""
    image_path_list = []
    for timepoint in file_handler[molecule + '/' + gene_name]:
        for image in file_handler[molecule + '/' + gene_name + '/' + timepoint]:
            if image_t in image:
                image_path = molecule + '/' + gene_name + '/' + timepoint + '/' + image
                image_path_list.append(image_path)
    return image_path_list



def print_attrs(name, obj):
    print(name)
    try:
        for key, val in obj.attrs.iteritems():
            print("    %s: %s" % (key, val))
    except IOError:
        print("Fail on name %s" % (name,))

def list_h5_file_content(h5_file):
    with h5py.File(h5_file, 'r') as h5_file:
        print(h5_file)
        print(list(h5_file.keys()))
        h5_file.visititems(print_attrs)
    return True

def get_cube(x):
    x = abs(x)
    return int(round(x ** (1. / 3)))

def calc_dist(p1,p2):
    return math.sqrt((p2[0] - p1[0]) ** 2 +
                     (p2[1] - p1[1]) ** 2 +
                     (p2[2] - p1[2]) ** 2)

def ripley_k_random_measure(IF,my_lambda,nuw,r_max):
    # make convolution in 2D - approximates 3D convolution as Z dimension is thin

    IF_2D=np.sum(IF,axis=2)
    IF_2D_rev = IF_2D[::-1,::-1]
    P=signal.convolve(IF_2D,IF_2D_rev)


    # distance map(dist from origin)
    dMap = np.zeros((512 * 2 - 1, 512 * 2 - 1))
    for x in range(512 * 2 - 1):
        for y in range(512 * 2 - 1):
            d = (x - 512) ** 2 + (y - 512) ** 2;
            dMap[x, y] = math.sqrt(d)


    # sum convolution using dMap
    K = np.zeros((constants.MAX_CELL_RADIUS, 1))
    for m in range(constants.MAX_CELL_RADIUS):
        K[m] = P[dMap[:,:] <= m].sum()
    K = K * (1 / (my_lambda ** 2 * nuw)) - (1 / my_lambda )
    return K

def ripley_k_point_process_2d(spots, my_lambda, nuw, r_max):
    n_spots = len(spots)
    K = np.zeros((r_max, 1))
    # add description
    for i in range(n_spots):
        ds = np.zeros((n_spots-1,1))
        for j in range(2):
            a = np.ma.array(spots[:, j], mask=False)
            a.mask[i] = True
            ds=np.add(ds.flatten(), np.square(spots[i, j] - a.compressed()))
        ds = np.sqrt(ds)
        if n_spots - 1 < r_max:
            for m in range(n_spots - 1):
                K[int(math.ceil(ds[m])):int(r_max)] = K[int(math.ceil(ds[m])):int(r_max)] + 1
        else:

            for m in range(r_max):
                K[m] = K[m] + ds[ds <= m].sum()
    K = K * (1 / (my_lambda**2 * nuw))
    return K

def ripley_k_point_process(spots, my_lambda, nuw, r_max):
    n_spots = len(spots)
    K = np.zeros((constants.MAX_CELL_RADIUS, 1))
    for i in range(n_spots):
        ds = np.zeros((n_spots-1,1))
        for j in range(3):
            a = np.ma.array(spots[:, j], mask=False)
            a.mask[i] = True
            if j==2:
                ds=np.add(ds.flatten(), np.square((spots[i, j] - a.compressed()) * constants.PIXELS_IN_SLICE))
            else:
                ds=np.add(ds.flatten(), np.square(spots[i, j] - a.compressed()))
        ds = np.sqrt(ds)
        if n_spots - 1 < r_max:
            for m in range(n_spots - 1):
                K[int(math.ceil(ds[m])):int(r_max)] = K[int(math.ceil(ds[m])):int(r_max)] + 1
        else:
            for m in range(r_max):
                K[m] = K[m] + ds[ds <= m].sum()
    K = K * (1 / (my_lambda**2 * nuw))
    return K



def clustering_index_random_measure(IF, cell_mask_3d):
    nuw = (np.sum(cell_mask_3d[:, :, :] == 1)) * constants.PIXELS_IN_SLICE
    my_lambda = float(np.sum(IF[:, :, :])) / float(nuw)
    k = ripley_k_random_measure(IF, my_lambda, nuw, constants.MAX_CELL_RADIUS)
    k_sim = np.zeros((constants.RIPLEY_K_SIMULATION_NUMBER, constants.MAX_CELL_RADIUS))

    # simulate n list of random spots and run ripley_k
    indsAll = np.where(cell_mask_3d[:, :, :] == 1)
    for t in range(constants.RIPLEY_K_SIMULATION_NUMBER):
        #print('simulation ', t)
        inds_permuted = np.random.permutation(range(len(indsAll[0])))
        I_samp=np.zeros(IF.shape)
        for u in range(len(inds_permuted)):
            new_x = indsAll[0][inds_permuted[u]]
            old_x = indsAll[0][u]
            new_y = indsAll[1][inds_permuted[u]]
            old_y = indsAll[1][u]
            new_z = indsAll[2][inds_permuted[u]]
            old_z = indsAll[2][u]
            I_samp[new_x,new_y,new_z]=IF[old_x,old_y,old_z]
        k_sim[t, :]=ripley_k_random_measure(I_samp,my_lambda,nuw,constants.MAX_CELL_RADIUS).flatten()

    h_star = np.zeros((constants.MAX_CELL_RADIUS, 1))
    h=k
    h_sim=k_sim
    h_sim_sorted = np.sort(h_sim)
    h_sim_sorted = np.sort(h_sim_sorted, axis=0)
    synth95 = h_sim_sorted[int(round(0.95 * constants.RIPLEY_K_SIMULATION_NUMBER)), :]
    synth50 = h_sim_sorted[int(round(0.5 * constants.RIPLEY_K_SIMULATION_NUMBER)), :]
    synth5 = h_sim_sorted[int(round(0.05 * constants.RIPLEY_K_SIMULATION_NUMBER)), :]

    # Compute delta between .95 percentile against .5 percentile
    delta1 = synth95 - synth50

    # Compute delta between .5 percentile against .05 percentile
    delta2 = synth50 - synth5

    inds = np.where(h == synth50)
    h_star[inds[0], :] = 0

    idx_sup = []
    for i in range(constants.MAX_CELL_RADIUS):
        if h[i, 0] > synth50[i]:
            idx_sup.append(i)
    if len(idx_sup) > 0:
        tmp = np.subtract(h[idx_sup, 0].astype(float), synth50[idx_sup].astype(float))
        tmp = tmp / delta1[idx_sup]
        h_star[idx_sup, 0] = tmp

    idx_inf = []
    for i in range(constants.MAX_CELL_RADIUS):
        if h[i, 0] < synth50[i]:
            idx_inf.append(i)
    if len(idx_inf) > 0:
        tmp = np.subtract(synth50[idx_inf].astype(float), h[idx_inf, 0].astype(float))
        tmp = - tmp / delta2[idx_inf]
        h_star[idx_inf, 0] = tmp

    h_star[h_star == - np.inf] = 0
    h_star[h_star == np.inf] = 0

    return h_star


# clustering index point process for muscle data
def clustering_index_point_process_2d(spots, cell_mask_2d,cell_radius):
    n_spots = len(spots)

    # Nuw is the whole volume of the cell
    nuw = (np.sum(cell_mask_2d[:, :] == 1)) * constants.SIZE_COEFFICIENT

    # spots volumic density
    my_lambda = float(n_spots) / float(nuw)
    k = ripley_k_point_process_2d(spots, my_lambda, nuw, cell_radius)
    k_sim = np.zeros((constants.RIPLEY_K_SIMULATION_NUMBER, cell_radius))

    #simulate n list of random spots and run ripley_k
    indsAll = np.where(cell_mask_2d[:, :] == 1)
    for t in range(constants.RIPLEY_K_SIMULATION_NUMBER):
        #print("simulation" + str(t))
        inds_permuted = np.random.permutation(range(len(indsAll[0])))
        indsT = inds_permuted[0:n_spots]
        spots_random = np.zeros(spots.shape)
        for i in range(len(spots)):
            spots_random[i, 0] = indsAll[0][indsT[i]]
            spots_random[i, 1] = indsAll[1][indsT[i]]
        tmp_k=ripley_k_point_process_2d(spots_random,my_lambda,nuw,cell_radius).flatten()
        k_sim[t,:]=tmp_k
    h_star=np.zeros((cell_radius,1))

    # Build related statistics derived from Ripley's K function
    # normalize K
    h = np.subtract(np.sqrt(k /  math.pi),np.arange(1, cell_radius + 1).reshape((cell_radius, 1)))
    h_sim = (np.sqrt(k_sim /  math.pi)) - matlib.repmat(np.matrix(np.arange(1, cell_radius + 1)), constants.RIPLEY_K_SIMULATION_NUMBER, 1)
    h_sim_sorted = np.sort(h_sim)
    h_sim_sorted=np.sort(h_sim_sorted[:,::-1],axis=0)
    synth95 = h_sim_sorted[int(round(0.95 * constants.RIPLEY_K_SIMULATION_NUMBER)), :]
    synth50 = h_sim_sorted[int(round(0.5 * constants.RIPLEY_K_SIMULATION_NUMBER)), :]
    synth5 = h_sim_sorted[int(round(0.05 * constants.RIPLEY_K_SIMULATION_NUMBER)), :]

    # Compute delta between .95 percentile against .5 percentile
    delta1 = synth95 - synth50

    # Compute delta between .5 percentile against .05 percentile
    delta2 = synth50 - synth5
    inds = np.where(h == synth50)
    h_star[inds[0], :] = 0
    idx_sup=[]
    for i in range(cell_radius):
        if h[i, 0] > synth50[0, i]:
            idx_sup.append(i)
    if len(idx_sup)>0:
        tmp = np.subtract(h[idx_sup, 0].astype(float),synth50[0, idx_sup].astype(float))
        tmp = tmp / delta1[0, idx_sup]
        h_star[idx_sup, 0] = tmp
    idx_inf = []
    for i in range(cell_radius):
        if h[i, 0] < synth50[0, i]:
            idx_inf.append(i)
    if len(idx_inf) > 0:
        tmp = np.subtract(synth50[0, idx_inf].astype(float), h[idx_inf, 0].astype(float))
        tmp = - tmp / delta2[0, idx_inf]
        h_star[idx_inf, 0] = tmp
    h_star[h_star == - np.inf] = 0
    h_star[h_star == np.inf] = 0
    return h_star


def clustering_index_point_process(spots, cell_mask_3d):
    n_spots = len(spots)
    # Nuw is the whole volume of the cell
    nuw = (np.sum(cell_mask_3d[:, :, :] == 1)) * constants.PIXELS_IN_SLICE
    #print (spots.shape)
    # spots volumic density
    my_lambda = float(n_spots) / float(nuw)
    k = ripley_k_point_process(spots, my_lambda, nuw, constants.MAX_CELL_RADIUS)
    k_sim = np.zeros((constants.RIPLEY_K_SIMULATION_NUMBER, constants.MAX_CELL_RADIUS))

    #simulate n list of random spots and run ripley_k
    indsAll = np.where(cell_mask_3d[:, :, :] == 1)
    for t in range(constants.RIPLEY_K_SIMULATION_NUMBER):
        #print("simulation"+str(t))
        inds_permuted = np.random.permutation(range(len(indsAll[0])))
        indsT = inds_permuted[0:n_spots]
        spots_random = np.zeros(spots.shape)
        for i in range(len(spots)):
            spots_random[i, 0] = indsAll[0][indsT[i]]
            spots_random[i, 1] = indsAll[1][indsT[i]]
            spots_random[i, 2] = indsAll[2][indsT[i]]
        tmp_k=ripley_k_point_process(spots_random,my_lambda,nuw,constants.MAX_CELL_RADIUS).flatten()
        k_sim[t,:]=tmp_k
    h_star=np.zeros((constants.MAX_CELL_RADIUS,1))

    # Build related statistics derived from Ripley's K function
    # normalize K
    h = np.subtract(np.power(((k * 3) / (4 * math.pi)), 1./3), np.arange(1,constants.MAX_CELL_RADIUS+1).reshape((constants.MAX_CELL_RADIUS, 1)))
    h_sim = (np.power(((k_sim * 3) / (4 * math.pi)), 1./3)) - matlib.repmat(np.matrix(np.arange(1,constants.MAX_CELL_RADIUS+1)), constants.RIPLEY_K_SIMULATION_NUMBER, 1)
    h_sim_sorted = np.sort(h_sim)
    h_sim_sorted=np.sort(h_sim_sorted[:,::-1],axis=0)
    synth95 = h_sim_sorted[int(round(0.95 * constants.RIPLEY_K_SIMULATION_NUMBER)), :]
    synth50 = h_sim_sorted[int(round(0.5 * constants.RIPLEY_K_SIMULATION_NUMBER)), :]
    synth5 = h_sim_sorted[int(round(0.05 * constants.RIPLEY_K_SIMULATION_NUMBER)), :]

    # Compute delta between .95 percentile against .5 percentile
    delta1 = synth95 - synth50

    # Compute delta between .5 percentile against .05 percentile
    delta2 = synth50 - synth5
    inds = np.where(h == synth50)
    h_star[inds[0], :] = 0
    idx_sup=[]
    for i in range(constants.MAX_CELL_RADIUS):
        if h[i, 0] > synth50[0, i]:
            idx_sup.append(i)
    if len(idx_sup)>0:
        tmp = np.subtract(h[idx_sup, 0].astype(float),synth50[0, idx_sup].astype(float))
        tmp = tmp / delta1[0, idx_sup]
        h_star[idx_sup, 0] = tmp
    idx_inf = []
    for i in range(constants.MAX_CELL_RADIUS):
        if h[i, 0] < synth50[0, i]:
            idx_inf.append(i)
    if len(idx_inf) > 0:
        tmp = np.subtract(synth50[0, idx_inf].astype(float), h[idx_inf, 0].astype(float))
        tmp = - tmp / delta2[0, idx_inf]
        h_star[idx_inf, 0] = tmp
    h_star[h_star == - np.inf] = 0
    h_star[h_star == np.inf] = 0
    #print(h_star)
    return h_star


# counter-clockwise rotate a point around the center_point; angle is in degrees
def rotate_point(center_point, point, angle):
    angle = math.radians(angle)
    temp_point = [point[0] - center_point[0], point[1] - center_point[1]]
    temp_point = (temp_point[0] * math.cos(angle) - temp_point[1] * math.sin(angle),
                  temp_point[0] * math.sin(angle) + temp_point[1] * math.cos(angle))
    temp_point = np.array([int(round(temp_point[0] + center_point[0])), int(round(temp_point[1] + center_point[1]))])
    return temp_point


def slope_from_points(point1, point2):
    if (point2[1] != point1[1]):
        return (point2[0].astype(np.float) - point1[0].astype(np.float)) / (
            point2[1].astype(np.float) - point1[1].astype(np.float))
    else:
        return 0


# Rotate a meshgrid clockwise by an angle
def rotate_meshgrid(xx, yy, radians=0):
    R = np.array([[np.cos(radians), np.sin(radians)],
                  [-np.sin(radians), np.cos(radians)]])
    return np.einsum('ji, mni -> jmn', R, np.dstack([xx, yy]))




def sign(point1, point2, point3):
    s = (point1[0] - point3[0]) * (point2[1] - point3[1]) - (point2[0] - point3[0]) * (point1[1] - point3[1])
    return s

def find_nearest(array, value):
    idx = (np.abs(array - value)).argmin()
    return idx


def prune_intensities(image,zero_level):
    IF_image_path = path.raw_data_dir + '/' + image.split('/')[2] + '/' + image.split('/')[1] + '_' + \
                         image.split('/')[3] + '/image_' + image.split('/')[4] + '/IF.tif'
    IF = io.imread(IF_image_path, plugin='tifffile')
    vol_block = np.zeros((512, 512, zero_level))
    for c_slice in range(0, zero_level):
        vol_block[:, :, c_slice] = IF[c_slice,:,:]
    return vol_block

