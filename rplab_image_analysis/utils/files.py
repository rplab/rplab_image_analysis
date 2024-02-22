"""
This module contains file functions that don't fall under the category of
file types determination or metadata. There's some grey area in there, but if
there's a file-related utility function that doesn't fit either of those, it
goes here.

Notes on this module: 

1. I would have made many of these functions methods of a subclass of 
pathlib.pathlib.Path, but subclassing pathlib.Path is a pain because of its 
"_flavor" attribute, used to differentiate between Posix and Windows file 
systems. Therefore, we have this module with functions that would gladly belong 
in a class.

2. All file functions in this module should support both str parameters
as well as pathlib.pathlib.Path. Generally, this is as easy as converting 
pathlib.Path objects to strings using str() or vice versa with pathlib.Path().
"""

import contextlib
import os
import pathlib
import shutil

import numpy as np
import psutil
import skimage.io
from natsort import natsorted
from tifffile import TiffFile

from rplab_image_analysis.utils import file_types

    
def copy_non_image_files(source_dir: str | pathlib.Path, 
                         dest_dir: str | pathlib.Path):
    """
    Copies non-image files in source_dir to dest_dir
    """
    source_dir = pathlib.Path(source_dir)
    dest_dir = pathlib.Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    for file in pathlib.Path(source_dir).iterdir():
        if not file_types.is_image(file):
            shutil.copy(file, dest_dir)
    

def copytree_ignore_images(source_dir: str | pathlib.Path, 
                           dest_dir: str | pathlib.Path
                           ):
    """
    Copies directory tree of source_dir using shutil.copytree() and ignores
    image files.

    ## Parameters:

    source_dir: str
        source directory to be copied.
    
    dest_dir: str
        destination directory that source_dir is copied to.
    """
    #*{file_extension} references all files with the given extension in a 
    #directory, so list below creates the ignore pattern to all image file 
    #types set in ImageFileType.
    #* to unpack list into arguments
    ignore_pattern = get_ignore_image_pattern()
    return shutil.copytree(
        source_dir, dest_dir, ignore=ignore_pattern, dirs_exist_ok=True)


def get_batch_path(source_dir: str | pathlib.Path, 
                   dest_dir: str | pathlib.Path, 
                   stem_suffix: str = ""
                   ) -> pathlib.Path:
    """
    returns save directory for batch processes.

    ### Example:
    >>> get_batch_dest_path("C:/Jonah/foo", "D:/Drake", "_dr")
    >>> 'D:/Drake/foo_dr'
    """
    stem = pathlib.Path(source_dir).stem
    dest_dir_path = pathlib.Path(dest_dir).joinpath(f"{stem}{stem_suffix}")
    return dest_dir_path


def get_dir_name(dir: str | pathlib.Path) -> str:
    """
    Returns directory name. If dir is a file path, returns name of parent
    directory.
    """
    dir = pathlib.Path(dir)
    if dir.is_dir():
        return pathlib.Path(dir).name
    elif dir.is_file():
        return pathlib.Path(dir).parent.name


def get_image_files(dir: str | pathlib.Path) -> list[str | pathlib.Path]:
    """
    Returns list of all image files in given directory.
    """
    dir_path = pathlib.Path(dir)
    files = []
    for file in dir_path.iterdir():
        with contextlib.suppress(TypeError):
            if file_types.is_image(file):
                files.append(str(file))
    #natsorted() sorts list so that files are sorted by number subscripts in
    #the correct order. ie, if there are 20 files named "image_1", "image_2",
    #..., order is "image_1", "image_2", ... "image_19" instead of "image_1",
    #"image_10", "image_11", ... "image_2", "image_3", ...
    files = natsorted(files)
    if isinstance(dir, pathlib.Path):
        files = [pathlib.Path(file) for file in files]
    return files


def get_ignore_image_pattern():
    ignore_list = [f"*{extn}" for extn in file_types.get_image_extns()]
    return shutil.ignore_patterns(*ignore_list)


def get_reduced_filename(file_path: str | pathlib.Path) -> str:
    file_path = pathlib.Path(file_path)
    filename = file_path.name
    filename = filename.split(file_types.FileSubtype.OME.value)[0]
    return filename


def get_save_path(file_path: pathlib.Path | str, 
                  source_path: pathlib.Path | str, 
                  dest_path: pathlib.Path | str,
                  stem_suffix: str = ""
                  ) -> pathlib.Path:
    """
    Returns file save path for batch processes. 

    ### Example:
    >>> get_save_path("C:/Jonah/fish/pos/foo.tif", "C:/Jonah", "D:/Drake", ")
    >>> 'D:/Drake/fish/pos/foo.tif'
    """
    file_path = pathlib.Path(file_path)
    source_path = pathlib.Path(source_path)
    dest_path = pathlib.Path(dest_path)
    rel_path = file_path.relative_to(source_path)
    dest_path = dest_path.joinpath(rel_path)
    dest_path = dest_path.with_stem(f"{dest_path.stem}{stem_suffix}")
    return dest_path


def get_sorted_dirs(path: pathlib.Path):
    """
    Returns natsorted directores from pathlib.Path.iterdir().
    """
    return natsorted([dir for dir in path.iterdir() if dir.is_dir()])


def get_walk_dir_list(source_path: pathlib.Path) -> list[pathlib.Path]:
    """
    Returns list of directory path objects found with os.walk(source_path).
    """
    subdirectories = []
    for root, dirs, files in os.walk(source_path):
        subdirectories.append(pathlib.Path(root))
    return subdirectories


def get_walk_image_lists(source_path: str | pathlib.Path
                         ) -> list[list[pathlib.Path]]:
    """
    Returns list of lists of image file path objects found in directories with 
    os.walk(source_path).
    """
    image_lists = []
    for root, dirs, files in os.walk(source_path):
        image_list = get_image_files(pathlib.Path(root))
        if image_list:
            image_lists.append(image_list)
    return image_lists


def in_use(file_path: str | pathlib.Path) -> bool:
    """
    Checks to see if file located at file_path is currently in use by process
    listed in psutil.processess_iter(). If file is in use, returns True. 
    Else, False.
    """
    file_path = str(file_path)
    for process in psutil.process_iter():
        try:
            for item in process.open_files():
                if file_path == item.path:
                    return True
        except Exception:
            pass
    return False


def is_other_image_files(file_path: str | pathlib.Path) -> bool:
    """
    If there are other image files in the parent directory of file_path 
    (according to image file types in ImageFileType class), returns True. 
    Else, returns False.
    """
    file_path = pathlib.Path(file_path)
    for file in file_path.parent.iterdir():
        if file_types.is_image(file) and not file_path.samefile(file):
            return True
    return False


def read_image(file_path: str | pathlib.Path) -> np.ndarray:
    """
    reads in images in file and returns them as ndarray.

    This is mostly here because tifffile loads in all images from all image 
    files that share metadata, which hogs memory. If file_path is a tif file,
    this loads in only the images stored in that file.
    """
    if file_types.get_file_type(file_path) == file_types.ImageFileType.TIF:
        stack = TiffFile(file_path)
        num_pages = len(stack.pages)
        image = stack.asarray(range(num_pages))
    else:
        image = skimage.io.imread(file_path)
    return image
    

def remove_file_extn(file_path: str | pathlib.Path) -> str | pathlib.Path:
    """
    Returns file_path with suffix removed.
    """
    path = pathlib.Path(file_path)
    path.with_suffix("")
    if isinstance(file_path, str):
        return str(path)
    elif isinstance(file_path, pathlib.Path):
        return path
    

def remove_mmstack(file_path: str | pathlib.Path) -> str | pathlib.Path:
    """
    removes "MMStack_" substring from Micro-Manager image filenames.

    If file_path is a str, returns str with "MMStack_" removed. If file_path 
    is a pathlib.Path, instead returns pathlib.Path with "MMStack_" removed.
    """
    file_name = str(file_path).replace(
        f"_{file_types.FileSubtype.MMSTACK.value}", "")
    if isinstance(file_path, str):
        return file_name
    elif isinstance(file_path, pathlib.Path):
        return pathlib.Path(file_name)
    

def remove_ome(file_path: str | pathlib.Path) -> str | pathlib.Path:
    """
    removes ".ome" substring from Micro-Manager image filenames.

    If file_path is a str, returns str with ".ome" removed. If file_path 
    is a pathlib.Path, instead returns pathlib.Path with ".ome" removed.
    """
    file_name = str(file_path).replace(file_types.FileSubtype.OME.value, "")
    if isinstance(file_path, str):
        return file_name
    elif isinstance(file_path, pathlib.Path):
        return pathlib.Path(file_name)
    

def save_image(save_path: str | pathlib.Path, 
               image: np.ndarray, 
               png_compression: int = 3):
    """
    Saves image at save_path. All filetypes supported by skimage are supported
    by this function.
    """
    if file_types.is_png(save_path):
        skimage.io.imsave(
            save_path, image, check_contrast=False, 
            compress_level=png_compression)
    else:
        skimage.io.imsave(save_path, image, check_contrast=False)
    

def yield_walk_image_files(source_path: str | pathlib.Path):
    """
    yields image file paths as pathlib.Path objects discovered through 
    os.walk(source_path).

    Note that this is a generator (not a list).
    """
    for root, dirs, files in os.walk(source_path):
        for file in files:
            if file_types.is_image(file):
                yield pathlib.Path(root).joinpath(file)


def yield_walk_image_files(source_path: str | pathlib.Path):
    """
    yields list of image files as pathlib.Path objects in each directory 
    discovered in os.walk(source_path).

    Note that this is a generator (not a list).
    """
    for root, dirs, files in os.walk(source_path):
        image_files = []
        for file in files:
            if file_types.is_image(file):
                image_files.append(pathlib.Path(root).joinpath(file))
        yield image_files


def yield_roots(source_path):
    """
    Calls provided function on each image file found in os.walk(source_path).
    Provided function should take a single argument (the file path).
    """
    for root, dirs, files in os.walk(source_path):
        yield pathlib.Path(root)
    