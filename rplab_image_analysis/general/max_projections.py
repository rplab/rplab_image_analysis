import os
import pathlib
import numpy as np
import skimage.io
import rplab_image_analysis.utils.files as files
from tifffile import TiffFile


def create_batch_max_projections(source_dir: str | pathlib.Path, 
                                 dest_dir: str | pathlib.Path
                                 ) -> str:
    """
    Creates max projection of all images in source_dir and all subdirectories
    and saves them in dest_dir. Also copies over directory structure of
    source_dir and copies over non-image files.

    ### Parameters:

    source_dir: str
        source directory of images.

    dest_dir: str
        directory where all images will be saved to.

    ### Returns:
    
    dest_path: str
        returns directory where images were written to.
    """
    source_path = pathlib.Path(source_dir)
    dest_path = files.get_batch_dest_path(
        source_path, dest_dir, suffix = "_max_projections")
    files.shutil_copy_ignore_images(source_path, dest_path)
    dirs = []
    for root, directories, filenames in os.walk(source_path):
        for filename in filenames:
            dirs.append(pathlib.Path(root))
    for dir in set(dirs):
        save_path = _get_dir_save_path(dir, source_path, dest_path)
        create_path_max_projection(dir, save_path)
    return str(dest_path)


def create_path_max_projection(path: str | pathlib.Path, 
                               save_path: str | pathlib.Path):
    """
    Creates max projection of images located at path and writes it to
    save_path.

    ### Parameters:

    path: str | pathlib.Path
        path can either be a file path or a directory. If it's a file path,
        only the specified file will be used in the max projection. If path
        is a directory, all image files directly inside directory will be
        used to create max projection.

    save_path: str | pathlib.Path
        file path that max projection will be saved to.
    """
    max_projection = get_max_projection(path)
    skimage.io.imsave(save_path, max_projection, check_contrast=False)


def get_max_projection(path: str | pathlib.Path) -> np.ndarray:
    """
    Creates max projection of images located at path and returns it as an
    ndarray. If you want the max projection of an ndarray already in Python,
    use np.max().

    path: str | pathlib.Path
        path can either be a file path or a directory. If it's a file path,
        only the specified file will be used in the max projection. If path
        is a directory, all image files directly inside directory will be
        used to create max projection.
    """
    path = pathlib.Path(path)
    if path.is_file():
        return _get_single_file_max_projection(path)
    elif path.is_dir():
        file_list = files.get_image_files_in_dir(path)
        return  _get_multifile_max_projection(file_list)


#create_batch_max_projections() helpers
def _get_dir_save_path(dir, source_path, dest_path):
    """
    Returns save path based on first file in dir.
    """
    file_path = files.get_image_files_in_dir(dir)[0]
    return files.get_save_path(file_path, source_path, dest_path)


#get_max_projection() helpers
def _get_single_file_max_projection(file_path: str | pathlib.Path):
    """
    Returns max_projection created from single image file.
    """
    file_type = files.get_file_type(file_path)
    if file_type == files.ImageFileType.TIF:
        return _get_tif_max_projection(file_path)
    elif file_type == files.ImageFileType.PNG:
        return skimage.io.imread(file_path)
    

def _get_multifile_max_projection(file_list: list[str | pathlib.Path]
                                  ) -> np.ndarray:
    """
    Iterates through files in file_list and creates a single maximum projection 
    from all image files.
    """
    for file_num, file in enumerate(file_list):
        new_image = _get_single_file_max_projection(file)
        if file_num == 0:
            max_projection = new_image
        max_projection = _get_two_image_max_projection(
            new_image, max_projection)
    return max_projection


def _get_tif_max_projection(file_path: str | pathlib.Path) -> np.ndarray:
    """
    Returns max projection from single tif stack
    """
    image_stack = TiffFile(file_path)
    for page_num, page in enumerate(image_stack.pages):
        new_image = page.asarray()
        if page_num == 0:
            max_projection = new_image
        else:
            max_projection = _get_two_image_max_projection(
                new_image, max_projection)
    return max_projection


def _get_two_image_max_projection(new_image: np.ndarray, 
                                  max_projection: np.ndarray
                                  ) -> np.ndarray:
    """
    Returns the max projection of new_image and max_projection
    """
    return np.max(np.array([new_image, max_projection]), 0)
