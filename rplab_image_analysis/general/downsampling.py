"""
This module contains code related to downsampling.
"""


import pathlib
import numpy as np

import skimage.transform

import rplab_image_analysis.utils.files as files


DS = "_ds"
DOWNSAMPLED = "_downsampled"


def downsample_batch(source_dir: str | pathlib.Path, 
                     dest_dir: str | pathlib.Path, 
                     downsample_factor: int = 1
                     ) -> str:
    """
    Downsamples all images in root_dir and all subdirectories in its structure.

    ### Paramaters:

    source_dir: str
        root_dir of images to be downsampled

    dest_dir: str 
        destination directory where downsampled images will be saved.
    
    downsample_factor: int
        sample that images will be downsampled by.

    ### Returns:
    
    dest_path: str
        returns directory where images were written to.
    """
    source_path = pathlib.Path(source_dir)
    dest_path = files.get_batch_path(source_path, dest_dir, DOWNSAMPLED)
    files.copytree_ignore_images(source_path, dest_path)
    for file in files.yield_walk_image_files(source_path):
        save_path = files.get_save_path(file, source_path, dest_path, DS)
        downsample_image_file(file, save_path, downsample_factor)
    return str(dest_path)


def downsample_image_file(file_path: str | pathlib.Path, 
                          save_path: str | pathlib.Path,
                          downsample_factor: int):
    """
    Downsamples image file by downsample factor.

    ### Paramaters:

    file_path: str | pathlib.Path
        path of image file.

    save_path: str | pathlib.Path
        path that downsampled image file will be saved to.
    
    downsample_factor: int
        factor that images will be downsampled by.
    """
    file_path = pathlib.Path(file_path)
    save_path = pathlib.Path(save_path)
    image = files.read_image(file_path)
    image = get_downsampled_image(image, downsample_factor)
    files.save_image(save_path, image)


def get_downsampled_image(image: np.ndarray, downsample_factor: int
                          ) -> np.ndarray:
    """
    downsamples an single image in (x,y) dimensions by downample_factor. 
    """
    dtype = image.dtype
    downsample_tuple = _get_downsample_tuple(image.ndim, downsample_factor)
    image = skimage.transform.downscale_local_mean(image, downsample_tuple)
    #downscale_local_mean returns float64, so must cast back to original dtype.
    return image.astype(dtype)


def _get_downsample_tuple(image_num_dims: int, ds_factor: int) -> tuple[int]:
    """
    Returns downsample tuple to be used with skimage downsacale_local_mean().
    Downsample tuple is created so that only dimensions that are downsampled
    are the image height and width.
    """
    downsample_list = [ds_factor, ds_factor]
    if image_num_dims > 2:
        for dim in range(image_num_dims - 2):
            #width and height are last two dimensions in any Micro-Manager 
            #image stack, and since we only want to downsample width and 
            #height, inserting 1 for all the other dimensions ignores them.
            downsample_list.insert(0, 1)
    return tuple(downsample_list)
    