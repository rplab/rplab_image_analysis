# %% [markdown]
# Author(s): Piyush Amitabh
# 
# Details: finds the pixel offset between BF image and saves it in a df_px_offset table
# 
# Created: May 16, 2023
# 
# License: GNU GPL v3.0
# 
# More info:  
# (1) uses cross-correlation between images to find the pixel offset
# 
# (2) coordinates are saved in skimage format - values are the shift *required* to get the offset image to the reference image

# %%
import os
import numpy as np
import skimage
from skimage import io
# from PIL import Image, TiffTags
import tifffile as tiff
from natsort import natsorted
import pandas as pd
from tqdm import tqdm

# %% [markdown]
# # User input

# %%
find_fix_flag = int(input('What do you want to do? (default = 1)\
                         1. Find and Fix pixel offset\
                         2. Only Find px offset (saves info in df)\
                         3. Only Fix px offset (uses info from saved df_px_offset)\n') or '1')
main_dir = input("Enter the location of Directory containing ONE fish data \n(this must contain BF/MIPs): ")
pos_max = int(input('Enter number of positions/regions of imaging per timepoint (default=4): ') or "4")

# %% [markdown]
# # Helping Functions

# %%
#removes dir and non-image(tiff) files from a list
def remove_non_image_files(big_list, root_path):
    small_list = []
    for val in big_list:
        if os.path.isfile(os.path.join(root_path, val)): #file check
            filename_list = val.split('.')
            og_name = filename_list[0] 
            ext = filename_list[-1] 
            if (ext=="tif" or ext=="tiff"): #img check
                small_list.append(val)
    return small_list

#correct the image list ordering
def reorder_image_by_pos_tp(img_list):
    ordered_img_list = []
    for tp in range(1, (len(img_list)//pos_max) + 1):
        for pos in range(1, pos_max+1):
            for img_name in img_list: #find the location in img_list with pos and tp
                if (f'pos{pos}_' in img_name.casefold()) and (f'timepoint{tp}_' in img_name.casefold()):
                    ordered_img_list.append(img_name)
    return(ordered_img_list)

#finds the target file nearest to the images
def find_nearest_target_file(target):
    '''finds nearest target file to the images in the dir structure
    returns the location of the found file'''
    #get start_path for search
    if gfp_flag:
        start_path = gfp_mip_path
    elif rfp_flag:
        start_path = rfp_mip_path
    elif bf_flag:
        start_path = bf_path

    target = 'df_px_offset.csv'
    while True:
        if os.path.isfile(os.path.join(start_path,target)):
            #found
            print(f'found {target} at:'+start_path)
            found_path = os.path.join(start_path,target)
            break

        if os.path.dirname(start_path)==start_path: #reached root
            #not found
            print("Error: Can't find notes.txt, Enter manually")
            found_path = input('Enter complete path (should end with .txt): ')
            break    
        start_path=os.path.dirname(start_path)
    return(found_path)

# #fixes offset
# def fix_offset(image, offset_image):
#     shift, error, diffphase = skimage.registration.phase_cross_correlation(image, offset_image)
#     print(shift) #gives shift in row, col <-> (y, x) of a std graph
#     tform = skimage.transform.SimilarityTransform(translation=shift[::-1]) #takes in the form (x,y)
#     warped = skimage.transform.warp(offset_image, tform.inverse)
#     return(warped)

# %%
#make a list of all 2D img files by channel
sub_names = ['BF', 'GFP', 'RFP']
bf_flag, gfp_flag, rfp_flag = False, False, False #0 means not found, 1 mean found
bf_path, gfp_mip_path, rfp_mip_path = '', '', ''
bf_img_list, gfp_img_list, rfp_img_list = [], [], []

for root, subfolders, filenames in os.walk(main_dir):
    for filename in filenames:
        # print(f'Reading: {filename}')
        filepath = os.path.join(root, filename)
        # print(f'Reading: {filepath}')
        filename_list = filename.split('.')
        og_name = filename_list[0] #first of list=name
        ext = filename_list[-1] #last of list=extension

        if (ext=="tif" or ext=="tiff"):
            if (not bf_flag) and ('bf' in og_name.casefold()): #find BF
                print('BF images found at:'+root)
                bf_path = root
                bf_img_list = reorder_image_by_pos_tp(remove_non_image_files(natsorted(os.listdir(root)), root))
                bf_flag = True
            elif 'mip' in og_name.casefold():
                if (not gfp_flag) and ('gfp' in og_name.casefold()):
                    print('GFP MIP images found at:'+root)
                    gfp_mip_path = root
                    gfp_img_list = reorder_image_by_pos_tp(remove_non_image_files(natsorted(os.listdir(root)), root))
                    gfp_flag = True
                elif (not rfp_flag) and ('rfp' in og_name.casefold()):
                    print('RFP MIP images found at:'+root)
                    rfp_mip_path = root
                    rfp_img_list = reorder_image_by_pos_tp(remove_non_image_files(natsorted(os.listdir(root)), root))
                    rfp_flag = True

if not bf_flag:
    print(f'No BF images found in {main_dir}')
if not gfp_flag:
    print(f'No GFP MIP images found in {main_dir}')
if not rfp_flag:
    print(f'No RFP MIP images found in {main_dir}')

# %% [markdown]
# # Find Offset

# %%
# # without mask
# if find_fix_flag==1 or find_fix_flag==2: #find offset and save in df_px_offset.csv
    
#     #Only need BF images
#     if not bf_flag:
#         print("Error: Cannot find the pixel offset without BF images")
#         exit()
    
#     print(f"Finding offset in BF images...")
#     save_path = os.path.join(os.path.dirname(bf_path), 'df_px_offset.csv')

#     # reference_img = [0]*pos_max
#     row_offset, col_offset = np.zeros_like(bf_img_list), np.zeros_like(bf_img_list)
#     tp_list, pos_list = np.zeros_like(bf_img_list), np.zeros_like(bf_img_list)

#     for i in range(pos_max): #read first timepoint images as reference images
#     #     reference_img[i] = tiff.imread(os.path.join(bf_path, bf_img_list[i]))
#         row_offset[i], col_offset[i] = 0, 0
#         tp_list[i] = 1
#         pos_list[i] = i+1

#     for i in tqdm(range(1, len(bf_img_list)//pos_max)): #run once per timepoint
#         # print(f"tp: {i+1}")
#         for j in range(pos_max):
#             loc = i*pos_max + j #gives the location in the list

#             prev_loc = (i-1)*pos_max + j
#             prev_row_offset, prev_col_offset = row_offset[prev_loc], col_offset[prev_loc]
#             # ref_img = tiff.imread(os.path.join(bf_path, bf_img_list[prev_loc])) #using previous img as ref doesn't work
#             prev_img = tiff.imread(os.path.join(bf_path, bf_img_list[prev_loc]))

#             #use corrected version of previous image as the reference image
#             tform = skimage.transform.SimilarityTransform(translation=(prev_col_offset, prev_row_offset))#only column _offset #takes in the form (x,y)
#             ref_img_uint = skimage.util.img_as_uint(skimage.exposure.rescale_intensity(skimage.transform.warp(prev_img, tform.inverse))) #rescale float and change dtype to uint16#corrected previous img

#             tp_list[loc] = i+1
#             pos_list[loc] = j+1
#             bf_offset_image = tiff.imread(os.path.join(bf_path, bf_img_list[loc])) #read present 2d image
#             # shift, error, diffphase = skimage.registration.phase_cross_correlation(reference_img[j], bf_offset_image)
#             shift, error, diffphase = skimage.registration.phase_cross_correlation(ref_img_uint, bf_offset_image)           
#             (row_offset[loc], col_offset[loc]) = shift # type: ignore #shift is in row, col <-> (y, x) of a std graph
#     df_px_offset = pd.DataFrame({'timepoint':tp_list, 'pos':pos_list, 'row_offset':row_offset, 'col_offset':col_offset})
#     df_px_offset.to_csv(save_path)

# %%
# using masks

if find_fix_flag==1 or find_fix_flag==2: #find offset and save in df_px_offset.csv
    
    #Only need BF images
    if not bf_flag:
        print("Error: Cannot find the pixel offset without BF images")
        exit()
    
    print(f"Finding offset in BF images...")
    save_path = os.path.join(os.path.dirname(bf_path), 'df_px_offset.csv')

    # reference_img = [0]*pos_max
    row_offset, col_offset = np.zeros_like(bf_img_list), np.zeros_like(bf_img_list)
    tp_list, pos_list = np.zeros_like(bf_img_list), np.zeros_like(bf_img_list)

    for i in range(pos_max): #read first timepoint images as reference images
    #     reference_img[i] = tiff.imread(os.path.join(bf_path, bf_img_list[i]))
        row_offset[i], col_offset[i] = 0, 0
        tp_list[i] = 1
        pos_list[i] = i+1

    for i in tqdm(range(1, len(bf_img_list)//pos_max)): #run once per timepoint
        # print(f"tp: {i+1}")
        for j in range(pos_max):
            loc = i*pos_max + j #gives the location in the list

            prev_loc = (i-1)*pos_max + j
            prev_row_offset, prev_col_offset = row_offset[prev_loc], col_offset[prev_loc]
            # ref_img = tiff.imread(os.path.join(bf_path, bf_img_list[prev_loc])) #using previous img as ref doesn't work
            prev_img = tiff.imread(os.path.join(bf_path, bf_img_list[prev_loc]))

            #use corrected version of previous image as the reference image
            tform = skimage.transform.SimilarityTransform(translation=(prev_col_offset, prev_row_offset))#only column _offset #takes in the form (x,y)
            ref_img_uint = skimage.util.img_as_uint(skimage.exposure.rescale_intensity(skimage.transform.warp(prev_img, tform.inverse))) #rescale float and change dtype to uint16#corrected previous img
            #generate mask correspongding to this image
            mask_i = np.ones_like(prev_img) #initial mask same as ref img
            mask = np.bool_(skimage.transform.warp(mask_i, tform.inverse))

            tp_list[loc] = i+1
            pos_list[loc] = j+1
            bf_offset_image = tiff.imread(os.path.join(bf_path, bf_img_list[loc])) #read present image
            # shift, error, diffphase = skimage.registration.phase_cross_correlation(reference_img[j], bf_offset_image)
            shift, error, diffphase = skimage.registration.phase_cross_correlation(ref_img_uint, bf_offset_image, reference_mask=mask, return_error='always')
            (row_offset[loc], col_offset[loc]) = shift # type: ignore #shift is in row, col <-> (y, x) of a std graph
    df_px_offset = pd.DataFrame({'timepoint':tp_list, 'pos':pos_list, 'row_offset':row_offset, 'col_offset':col_offset})
    df_px_offset.to_csv(save_path)

# %% [markdown]
# # Fix Offset

# %%
if find_fix_flag==1 or find_fix_flag==3: #fix offset 

    df = pd.read_csv(find_nearest_target_file('df_px_offset.csv'))

    #read all images per timepoint then fix offset and save them at dest 
    ch_flag_list = [bf_flag, gfp_flag, rfp_flag]
    ch_path_list = [bf_path, gfp_mip_path, rfp_mip_path]
    ch_img_list = [bf_img_list, gfp_img_list, rfp_img_list]

    for k, ch_flag in enumerate(ch_flag_list):
        all_img_list = ch_img_list[k]
        ch_path = ch_path_list[k]
        ch_name = sub_names[k]

        if ch_flag:
            print(f"Fixing offset in {ch_name} images...")
            save_path = os.path.join(ch_path, ch_name.casefold()+'_offset_corrected')
            if not os.path.exists(save_path): #check if the dest exists
                print("Save path doesn't exist.")
                os.makedirs(save_path)
                print(f"Directory '{ch_name.casefold()}_offset_corrected' created")
            else:
                print("Save path exists")

            for i in tqdm(range(len(all_img_list)//pos_max)): #run once per timepoint
                tp = i+1
                img_list_per_tp = [0]*pos_max
                for j in range(0, pos_max):
                    loc = i*pos_max + j
                    p = j+1
                    single_2d_img = tiff.imread(os.path.join(ch_path, all_img_list[loc])) #save a single 2D image
                    # get its value from the df_px_offset
                    filt = (df['pos']==p) & (df['timepoint']==tp)
                    r_offset = df['row_offset'][filt].values[0]
                    c_offset = df['col_offset'][filt].values[0]
                    tform = skimage.transform.SimilarityTransform(translation=(c_offset, 0))#only column _offset #takes in the form (x,y)
                    warped_img_uint = skimage.util.img_as_uint(skimage.exposure.rescale_intensity(skimage.transform.warp(single_2d_img, tform.inverse))) #rescale float and change dtype to uint16
                    tiff.imwrite(os.path.join(save_path, all_img_list[loc]), warped_img_uint) #save the image

# %% [markdown]
# ---


