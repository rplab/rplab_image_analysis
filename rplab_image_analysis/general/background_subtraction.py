import os
import pathlib
import numpy as np
import skimage.io
import rplab_image_analysis.utils.files as files


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
    """
    source_path = pathlib.Path(source_dir)
    dest_path = files.get_batch_dest_path(
        source_path, dest_dir, suffix = "_background_subtracted")
    files.shutil_copy_ignore_images(source_path, dest_path)
    for root, directories, filenames in os.walk(source_path):
        for filename in filenames:
            if files.get_file_type(filename) in files.ImageFileType:
                file_path = pathlib.Path(root).joinpath(filename)
                save_path = files.get_save_path(
                    file_path, source_path, dest_path, "_bs")
                median_subtract_image_file(file_path, save_path)
    return str(dest_path)


def median_subtract_image_file(file_path: str | pathlib.Path, 
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
    image = files.read_images(file_path)
    image = get_median_subtracted_image(image)
    skimage.io.imsave(save_path, image)


def get_median_subtracted_image(image: np.ndarray) -> np.ndarray:
    """
    calculates background as median of image/image stack subtracts it
    from image. Returns image with background subtracted as ndarray.
    """
    dtype = image.dtype
    background = int(np.median(image))
    image = image.astype(np.int16)
    image -= background
    image[image < 0] = 0
    return image.astype(dtype)
