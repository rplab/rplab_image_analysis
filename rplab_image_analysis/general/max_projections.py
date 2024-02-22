import pathlib

import numpy as np
from tifffile import TiffFile

from rplab_image_analysis.utils import files, file_types


MAX = "_max"
MAX_PROJ = "_max_projections"


def max_batch(source_dir: str | pathlib.Path, 
              dest_dir: str | pathlib.Path
              ) -> str:
    """
    Creates max projection of all images in source_dir and all subdirectories
    and saves them in dest_dir. Also copies over directory structure of
    source_dir and copies over non-image files.

    For batch processing, assumes that all files in a single directory should
    be used to create a single projection. If a Micro-manager multi-channel,
    multipage tif was taken, must be split into separate channels before
    batch processing.

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
    dest_path = files.get_batch_path(source_path, dest_dir, MAX_PROJ)
    for dir in files.yield_roots(source_path):
        files.copy_non_image_files(dir, dest_dir)
        file_list = files.get_image_files(dir)
        _get_max_from_list(file_list, dest_path)
    return str(dest_path)


def create_max(file_path: str | pathlib.Path, 
               save_path: str | pathlib.Path):
    """
    Creates max projection of image located at file_path and writes it to
    save_path. If file_path is a tif stack, only uses images in file at
    file_path, not in other images files in same series.

    ### Parameters:

    file_path: str | pathlib.Path | list[str | pathlib.Path]
        path can be a file path, directory, or list of files. If path is a file 
        path, only the image file passed will be used to produce max 
        projection. If path is directory, all files in the directory will be
        used.

    save_path: str | pathlib.Path
        file path that max projection will be saved to.
    """
    file_path = pathlib.Path(file_path)
    save_path = pathlib.Path(save_path)
    save_path.parent.mkdir(parents = True, exist_ok=True)
    files.copy_non_image_files(file_path, save_path)
    max_projection = get_max(file_path)
    files.save_image(save_path, max_projection)


def create_max_from_list(file_list: list[str | pathlib.Path], 
                         save_path: str | pathlib.Path):
    """
    Creates max projection of images in file_list and writes it to save_path.
    All images in file_list will be used to create the same max projection.

    ### Parameters:

    path: str | pathlib.Path
        path can be a file path or directory. If path is a file path, only the 
        image file passed will be used to produce max projection. If path is 
        directory, all images from same series will be used.

    save_path: str | pathlib.Path
        file path that max projection will be saved to.
    """
    file_list = [pathlib.Path(f) for f in file_list]
    save_path = pathlib.Path(save_path)
    save_path.parent.mkdir(exist_ok=True)
    files.copy_non_image_files(file_list[0].parent, save_path)
    max_projection = _get_max_from_list(file_list)
    files.save_image(save_path, max_projection)


def get_max(file_path: str | pathlib.Path) -> np.ndarray:
    """
    Creates max projection of images located at path and returns it as an
    ndarray. If you want the max projection of an ndarray already in Python,
    use np.max().

    file_path: str | pathlib.Path
        path of image file.
    """
    file_path = pathlib.Path(file_path)
    if file_types.is_tif(file_path):
        return _get_tif_max(file_path)
    else:
        return files.read_image(file_path)


def _get_max_from_list(file_list: list[str | pathlib.Path]
                       ) -> np.ndarray:
    """
    Iterates through files in file_list and creates a single maximum 
    projection from all image files.
    """
    max_proj = None
    for file in file_list:
        new_image = get_max(file)
        max_proj = _update_max_proj(max_proj, new_image)
    return max_proj


def _get_tif_max(file_path: str | pathlib.Path) -> np.ndarray:
    """
    Returns max projection from single tif stack
    """
    image_stack = TiffFile(file_path)
    max_proj = None
    for page in image_stack.pages:
        new_image = page.asarray()
        max_proj = _update_max_proj(max_proj, new_image)
    return max_proj


def _update_max_proj(max_proj: np.ndarray, 
                     new_image: np.ndarray
                     ) -> np.ndarray:
    """
    Returns the np.max of new_image and max_proj. max_proj is intended to be
    the current max projection and this should be used to update max_proj.
    If max_proj is none, will just return new_image.
    """
    if not max_proj:
        return new_image
    return np.max(np.array([new_image, max_proj]), 0)
    