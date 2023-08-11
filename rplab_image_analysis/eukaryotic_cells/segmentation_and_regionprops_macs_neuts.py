# %% [markdown]
# Author(s): Piyush Amitabh
# 
# Details: this code downsamples, segments neutrophils and macrophages, saves regionprops to csv
# 
# Created: March 31, 2022
# 
# License: GNU GPL v3.0

# %% [markdown]
# ---
# %% [markdown]
# Created: Dec 06, 2022
# From: segmentation_and_regionprops_surface area_v2.ipynb
# Comments:
# - Batch processes downsampled images and saves their region properties
# - regionprops list updated for skimage-v0.19.2

# Updated: v9 on Feb 15, 2023
# Comments: made code os agnostic. As long as the original path is given correctly the code should work on windows or linux.
#
# date: mar 23, 23
# extended for macrophages
#
# date: Aug 11, 23
# - derived from v9 of the code by same name
# - removed the save in same folder option
# %% [markdown]
# ---

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import ndimage as ndi # type: ignore

import skimage
from PIL import Image, TiffTags
import tifffile as tiff
import os

from tqdm import tqdm
from natsort import natsorted
import shutil
# import gc


# %% [markdown]
# # helper functions and constants

# %%
#function to enhance and show images
def show_image(img, img_title='', color=False, max_contrast=False):
    fig = plt.figure(figsize=(20,15))
    img = np.array(img)
    if max_contrast==True:
        enhance = skimage.exposure.equalize_hist(img) # type: ignore
    else:
        enhance = img
    if color==False:
        plt.imshow(enhance, cmap='gray')
    else:
        plt.imshow(enhance)
    plt.title(img_title)
    plt.colorbar()
    plt.axis("off")
    plt.show()

# %%
#find the stats of array (can take time)
def find_stats(ar):
    mean_xtrain = np.mean(ar)
    std_xtrain = np.std(ar)
    max_xtrain = np.max(ar)
    min_xtrain = np.min(ar)
    print(f'Stats: mean={mean_xtrain:.3f}, std={std_xtrain:.3f}, min={min_xtrain}, max={max_xtrain}')

# %% [markdown]
# The pixel spacing in this dataset is 1µm in the z (leading!) axis, and  0.1625µm in the x and y axes.

# %%
n = 4 #downscaling factor in x and y
zd, xd, yd = 1, 0.1625, 0.1625 #zeroth dimension is z
orig_spacing = np.array([zd, xd, yd]) #change to the actual pixel spacing from the microscope
new_spacing = np.array([zd, xd*n, yd*n]) #downscale x&y by n

# # %%
# img_val = listfiles[0]
# stack_full = tiff.imread(os.path.join(dir_path, img_val))

# %% [markdown]
# # Loop over all images and save info
#

# %%
# list of regionprops updated for skimage-v0.19.2

def get_info_table_neuts(img_path):
    '''Reads images given by img_path and returns segmented obj labels and regionprops table as pandas dataframe'''
    
    stack_full = tiff.imread(img_path)
    if len(stack_full.shape)!=3: #return None if not a zstack
        return(None, None)
    print('Reading: '+img_path)

    denoised = ndi.median_filter(stack_full, size=3)
    simple_thresh = denoised>1200 # type: ignore #manual value
    
    # mean=np.mean(stack_full) #try median, very close values doesn't matter
    # std=np.std(stack_full)
    # thresh_val = mean + 5*std
    # simple_thresh = denoised>thresh_val # type: ignore #based on image values

    labels = skimage.measure.label(simple_thresh) # type: ignore #labels is a bool image
    info_table = pd.DataFrame(
        skimage.measure.regionprops_table( # type: ignore
            labels, 
            intensity_image=stack_full, 
            properties=['label', 'centroid', 'centroid_weighted',  'area', 'equivalent_diameter_area', 'intensity_mean']#, #'slice','moments_normalized', 'coords'
        )
    ).set_index('label')
    return(labels, info_table)

# %%
def filter_info_table_neuts(labels, info_table):
    '''filters info table obtained by get_info_table according to obj properties defined below'''

    #filter by volume removing small objects
    # voxel_width = 3/(0.1625**2) #corresponding to 3um^3
    voxel_width = 10 ** 3 #1000 -> 26.5 um^3

    info_table_filt = info_table[info_table.area>voxel_width].copy()

    #generate label for the filtered table
    bad_label = list(set.difference(set(info_table.index), set(info_table_filt.index)))
    filt_labels = labels.copy()

    for i in bad_label:
        filt_labels[np.where(labels==i)] = 0

    return(filt_labels, info_table_filt)

def get_info_table_macs(img_path):
    '''Reads images given by img_path and returns segmented obj labels and regionprops table as pandas dataframe'''
    
    stack_full = tiff.imread(img_path)
    if len(stack_full.shape)!=3: #return None if not a zstack
        return(None, None)
    print('Reading: '+img_path)

    denoised = ndi.median_filter(stack_full, size=3)

    mean=np.mean(stack_full) #try median
    std=np.std(stack_full)
    thresh_val = mean + 10*std
    simple_thresh = denoised>thresh_val # type: ignore #manual value
    # simple_thresh = denoised>1000 # type: ignore #manual value
    
    dilated_high_thresh = ndi.binary_dilation(simple_thresh, iterations=5)
    skeleton = skimage.morphology.skeletonize(dilated_high_thresh) # type: ignore
    connected_regions = np.logical_or(simple_thresh, skeleton)
    labels = skimage.measure.label(connected_regions) # type: ignore
    
    info_table = pd.DataFrame(
        skimage.measure.regionprops_table( # type: ignore
            labels, 
            intensity_image=stack_full, 
            properties=['label', 'centroid', 'centroid_weighted',  'area', 'equivalent_diameter_area', 'intensity_mean']#, #'slice','moments_normalized', 'coords'
        )
    ).set_index('label')
    return(labels, info_table)

# %%
def filter_info_table_macs(labels, info_table):
    '''filters info table obtained by get_info_table according to obj properties defined below'''

    #filter by volume removing small objects
    # voxel_width = 3/(0.1625**2) #corresponding to 3um^3
    voxel_width_min = (10 ** 3)/2 #1000/2 -> 26.5/2 um^3
    voxel_width_max = 10 ** 5
    
    info_table_filt = info_table[np.logical_and(info_table.area>voxel_width_min,  info_table.area<voxel_width_max)].copy()

    #generate label for the filtered table
    bad_label = list(set.difference(set(info_table.index), set(info_table_filt.index)))
    filt_labels = labels.copy()

    for i in bad_label:
        filt_labels[np.where(labels==i)] = 0

    return(filt_labels, info_table_filt)

# %%
def find_surface_area(filt_labels, info_table_filt):
    '''Uses marching cubes to find the surface area of the objects in info_table_filt
    Adds this user_surface_area and sphericity to the info_table_filt'''

    list_surface_area = []

    for selected_cell in range(len(info_table_filt.index)):
        regionprops = skimage.measure.regionprops(filt_labels.astype('int')) # type: ignore
        # skimage.measure.marching_cubes expects ordering (row, col, pln)
        volume = (filt_labels == regionprops[selected_cell].label).transpose(1, 2, 0)
        verts, faces, _, values = skimage.measure.marching_cubes(volume, level=0, spacing=(1.0, 1.0, 1.0)) # type: ignore
        surface_area_pixels = skimage.measure.mesh_surface_area(verts, faces) # type: ignore
        list_surface_area.append(surface_area_pixels)

    # print('found surface area')
    info_table_filt['user_surface_area'] = list_surface_area
    info_table_filt['sphericity'] = np.pi*np.square(info_table_filt['equivalent_diameter_area'])/info_table_filt['user_surface_area']

# %%
def segment_save_props_ds(img_path, save_path, csv_name):
    """
    Description:
    Reads downsampled images given by 'img_path', finds properties and saves them in 'csv_name' at 'save_path'
    """
    if 'rfp' in img_path.casefold():
        #get info_table
        labels, info_table = get_info_table_macs(img_path)
        if np.all(labels==None): #return for non-zstacks
            return
        #filter info_table
        filt_labels, info_table_filt = filter_info_table_macs(labels, info_table)
    elif 'gfp' in img_path.casefold():
        #get info_table
        labels, info_table = get_info_table_neuts(img_path)
        if np.all(labels==None): #return for non-zstacks
            return
        #filter info_table
        filt_labels, info_table_filt = filter_info_table_neuts(labels, info_table)
    else:
        print("ERROR: img location name must have gfp or rfp keywords")
        exit()
    #add custom surface area
    find_surface_area(filt_labels, info_table_filt)

    info_table_filt.to_csv(os.path.join(save_path, csv_name))
    print('Successfully saved: '+csv_name)

# %% [markdown]
# ## Save region props for all the time points


# %% [markdown]
# change below directory structure to point to zstack images in two separate folders "GFP" and "RFP"


# %%
main_dir = input('Enter the Main directory containing ALL images to be segmented: ')

sub_dirs = ['GFP', 'RFP'] #as we can only segment in fluorescent channels

print('Images need to be sorted in different directories by channel(BF/GFP/RFP).')
print('Else this code will give erroneous results..')
flag = input('Continue? (y/n)')
if flag.casefold().startswith("y"):
    print('ok, starting segmentation')
else:
    print('Okay, bye!')
    exit()

#now do os walk then send all images to the segment function to starting segmentation
for root, subfolders, filenames in os.walk(main_dir):
    for filename in filenames:        
        filepath = os.path.join(root, filename)
        # print(f'Reading: {filepath}')
        filename_list = filename.split('.')
        og_name = filename_list[0] #first of list=name
        ext = filename_list[-1] #last of list=extension

        if ext=="tif" or ext=="tiff": #only if tiff file
            #check image channel and create directory if it doesn't exist
            for sub in sub_dirs:
                if sub.casefold() in og_name.casefold(): #find the image channel 
                    segment_save_props_ds(img_path=filepath, save_path=root, csv_name=og_name+'_info.csv')

# %% [markdown]
# # Analysis and Linking

# %% [markdown]
# see: analysis_n_linking.ipynb

# %% [markdown]
# ---