import pathlib

import numpy as np

import rplab_image_analysis.utils.files as files


MS = "_ms"
MED_SUB = "_median_subtracted"


def median_subtract_batch(source_dir: str | pathlib.Path, 
                          dest_dir: str | pathlib.Path
                          ) -> str:
    """
    subtracts background all images in root_dir and all subdirectories in its 
    structure.

    ### Paramaters:

    source_dir: str
        root_dir of images to be downsampled

    dest_dir: str 
        destination directory where downsampled images will be saved.

    ### Returns:
    
    dest_path: str
        returns directory where images were written to.
    """
    source_path = pathlib.Path(source_dir)
    dest_path = files.get_batch_path(source_path, dest_dir, MED_SUB)
    files.copytree_ignore_images(source_path, dest_path)
    for file in files.yield_walk_image_files(source_path):
        save_path = files.get_save_path(file, source_path, dest_path, MS)
        create_median_subtracted(file, save_path)
    return str(dest_path)


def create_median_subtracted(file_path: str | pathlib.Path, 
                             save_path: str | pathlib.Path):
    """
    Subtracts background from image file located at file_path and saves
    it to save_path.

    ###Parameters:

    file_path: str | pathlib.Path
        file path of image file.
    
    save_path: str | pathlib.Path
        file path that image will be saved to.
    """
    image = files.read_image(file_path)
    image = get_median_subtracted_image(image)
    files.save_image(save_path, image)
    

def get_median_subtracted_image(image: np.ndarray) -> np.ndarray:
    """
    calculates background as median of image/image stack subtracts it
    from image. Returns image with background subtracted as ndarray.
    """
    dtype = image.dtype
    background = int(np.median(image))
    image = image.astype(np.int32)
    image -= background
    image[image < 0] = 0
    return image.astype(dtype)
