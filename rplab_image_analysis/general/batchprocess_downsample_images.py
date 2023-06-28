# %%
# from pathlib import Path
import shutil
import os

# %%
import numpy as np
import skimage
from skimage import io
# from PIL import Image, TiffTags
import tifffile as tiff

# %%
# get user input for source and dest
src = os.path.normpath(input("Enter the Parent folder for original images: "))
trg = os.path.normpath(input("Enter the Destination for saving downsampled images: "))

print(f'Source Dir: {src}')
print(f'Target Dir: {trg}')
flag = input('Is this correct? (default-y/n):') or 'y'
if(flag.casefold()!='y'):
    exit()

# %%
new_folder_name = os.path.split(src) + '_downsampled'
new_trg_path = os.path.join(trg, new_folder_name)
os.mkdir(new_trg_path)
print(f'made dir: {new_trg_path}')

# %% [markdown]
# Assuming the folder structure is of the form: 
# 
# src dir -> Acquisition dir -> {fish1 dir, fish2 dir, etc.} + notes.txt

# %%
new_src_path = os.path.join(src, 'Acquisition')
if os.path.exists(new_src_path):
    print('...')
    print(f'The first level of directory structure inside-\n {new_src_path}\nwill be copied along with any metadata at this level')
    print('...')
else:
    print("ERROR: The Source folder MUST have 'Acquisition' folder inside it")
    print("Exiting Now...")
    exit()
files = os.listdir(new_src_path)

for filename in files:
    filename_list = filename.split('.')
    og_name = filename_list[0] #first of list=name
    ext = filename_list[-1] #last of list=extension

    if ext=="txt": #copy text files
        shutil.copy(os.path.join(new_src_path,filename), new_trg_path)
        print(f'copied file: {filename}')
    else: #make folders
        os.mkdir(os.path.join(new_trg_path, filename))
        print(f'made dir: {filename}')

# %% [markdown]
# The pixel spacing in this dataset is 1µm in the z (leading!) axis, and  0.1625µm in the x and y axes.
# 
# n is the downscaling factor in x and y, change it accordingly.

# %%
n = input('Enter downscaling factor for x and y dimensions (hit enter for default=4):') or 4
if type(n)!=int or n<=0:
    print('User Error: downscaling factor has to be a positive integer')
    exit()

# %%
def read_n_downscale_image(read_path):
    print(f'Reading: {read_path}')
    img = tiff.imread(read_path)
    print(f'Shape of read image {img.shape}')
    if len(img.shape)==2: #2 dimensional image, e.g. BF image
        img_downscaled = skimage.transform.downscale_local_mean(img, (n, n)) #use a kernel of nxn, ds by a factor of n in x & y
    elif len(img.shape)==3: #image zstack
        img_downscaled = skimage.transform.downscale_local_mean(img, (1, n, n)) #use a kernel of 1xnxn, no ds in z
    else:
        print("Can't process images with >3dimensions")
        return(None)
    return(skimage.util.img_as_uint(skimage.exposure.rescale_intensity(img_downscaled)))

# %%
for root, subfolders, filenames in os.walk(new_src_path):
    for filename in filenames:
        # print(f'Reading: {filename}')
        filepath = os.path.join(root, filename)
        # print(f'Reading: {filepath}')
        filename_list = filename.split('.')
        og_name = filename_list[0] #first of list=name
        ext = filename_list[-1] #last of list=extension

        if ext=="tif" or ext=="tiff": #only compress tiff files (prevents compression of other filetypes)
            # print(f'Reading Image: {filepath}')
            fish_num = og_name[og_name.find('fish')+4]
            save_path = os.path.join(new_trg_path, 'fish'+str(fish_num)) #save the ds images sorted by fish number
            if og_name.endswith('_MMStack'): #remove 'MMStack' in saved name
                save_name = og_name[:-len('_MMStack')]+'_ds.'+ext
            else:
                save_name = og_name+'_ds.'+ext
            tiff.imwrite(os.path.join(save_path, save_name), read_n_downscale_image(read_path=filepath))
# %% [markdown]
# ---


