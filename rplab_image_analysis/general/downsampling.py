import os
import numpy as np
import skimage
import skimage.io
import tifffile
from utils.files import FileType, get_file_type, shutil_copy_ignore_images

def downsample_images(root_dir: str, 
                      dest_path: str, 
                      downsample_factor: int
    ) -> str:
    """
    Downsamples all images in root_dir and all subdirectories in its structure.

    ### Paramaters:

    root_dir: str
        root_dir of images to be downsampled

    dest_path: str 
        destination directory where downsampled images will be saved.
    
    downsample_factor: int
        sample that images will be downsampled by. Note that the only 
        dimensions downsampled will be the width and height of the image.
    """
    original_folder_name = root_dir.split('\\')[-1]
    new_folder_name = f"{original_folder_name}_downsampled"
    new_dest_path = os.path.join(dest_path, new_folder_name)
    os.mkdir(new_dest_path)
    shutil_copy_ignore_images(root_dir, new_dest_path)
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            filepath = os.path.join(root, file)
            if get_file_type(filepath) == FileType.TIF:
                image = tifffile.TiffFile(filepath).asarray()
                downsampled_image = downsample_image(image, downsample_factor)
                #relpath returns path of file relative to start
                rel_path = os.path.relpath(filepath, root_dir)
                save_path = os.path.join(
                    rel_path, f"{new_dest_path}_ds{FileType.TIF.value}")
                tifffile.imwrite(save_path, downsampled_image)
            elif get_file_type(filepath) == FileType.PNG:
                image = skimage.io.imread(filepath)
                downsampled_image = downsample_image(image, downsample_factor)
                #relpath returns path of file relative to start
                rel_path = os.path.relpath(filepath, root_dir)
                save_path = os.path.join(
                    rel_path, f"{new_dest_path}_ds{FileType.PNG}")
                skimage.io.imwrite(save_path, downsampled_image)
    return new_dest_path

def downsample_image(image: np.ndarray, downsample_factor) -> np.ndarray:
    """
    downsamples one image passed in as an ndarray in (x,y) dimensions
    by downample_factor. Returns 
    """
    downsample_tuple = _get_downsample_tuple(
        len(image.shape), downsample_factor)
    return skimage.transform.downscale_local_mean(image, downsample_tuple)
    
def _get_downsample_tuple(image_num_dims, downsample_factor) -> tuple[int]:
    n = downsample_factor
    downsample_list = [n, n]
    if image_num_dims > 2:
        for dim in range(image_num_dims-2):
            downsample_list.insert(0, 1)
    return tuple(downsample_list)
    