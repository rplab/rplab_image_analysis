"""
Notes on this module: 

1. I would have made so many of these functions methods of
a subclass of pathlib.pathlib.Path, but subclassing pathlib.Path is really annoying because
of its "_flavor" attribute, used to differentiate between Posix and Windows 
file systems. Therefore, we have this module with functions that would gladly 
belong in a class. Sigh.

2. All file system functions in this module should support both str parameters
as well as pathlib.pathlib.Path. Generally, this is as easy as converting pathlib.Path objects
to strings using str() or vice versa with pathlib.Path().
"""


import contextlib
import pathlib
import shutil
import psutil
import numpy as np
import skimage.io
from enum import Enum
from natsort import natsorted
from tifffile import TiffFile


class ImageFileType(Enum):
    """
    Enum class with constants representing image file type, which is determined
    by file extension.

    Current assumptions are that all image file types are supported by 
    skimage's io module, so that imread and imwrite work. If this ends up
    not being the case, separate implementation will need to be applied for 
    those image file extensions that aren't supported.
    """
    TIF: str = [".tif", ".tiff"]
    PNG: str = [".png"]


class OtherFileType(Enum):
    TXT: str = ".txt"


class FileSubtype(Enum):
    """
    Enum class with constants representing file subtype, which is determined
    by substrings in filename, such as "MMStack" for Micro-Manager tif stack 
    images and "metadata" for Micro-Manager metadata files. 
    """
    MMSTACK: str = "MMStack"
    METADATA: str = "metadata"
    LS_NOTES: str = "notes"
    OME: str = "ome"


#functions to determine file type
def get_file_type(file_path: str | pathlib.Path) -> ImageFileType:
    """
    Gets file type, determined by file extension.

    ### Paramaters:

    file_path: str

    ### Returns:

    file_type: FileType
        file type of file at file_path.
    """
    file_extn = get_file_extn(file_path)
    if file_extn == OtherFileType.TXT.value:
        return OtherFileType.TXT
    for extn in ImageFileType.TIF.value:  
        if file_extn == extn:
            return ImageFileType.TIF
    for extn in ImageFileType.PNG.value:  
        if file_extn == extn:
            return ImageFileType.PNG


def get_file_subtype(file_path: str | pathlib.Path) -> FileSubtype:
    """
    Gets subtype of file. Subtype is the location/context from where that file
    was generated.

    For example, a file with subtype MMSTACK is a tif stack file generated
    by Micro-Manager.

    ### Parameters:

    file_path: str

    ### Returns:

    file_subtype: FileSubtype
        file subtype of file at file_path.
    """
    file_path = str(file_path)
    file_type = get_file_type(file_path)
    if file_type == ImageFileType.TIF and FileSubtype.MMSTACK.value in file_path:
        return FileSubtype.MMSTACK
    if file_type == OtherFileType.TXT:
        if FileSubtype.METADATA.value in file_path:
            return FileSubtype.METADATA
        elif FileSubtype.LS_NOTES.value in file_path:
            return FileSubtype.LS_NOTES
        

def get_image_extns() -> list:
    """
    Returns list with all image file extensions.
    """
    extn_lists = [extn.value for extn in ImageFileType]
    return [extn for ftype in extn_lists for extn in ftype]


def remove_image_extn(file_path) -> str | pathlib.Path:
    file_name = str(file_path)
    for extn in get_image_extns():
        if file_name.endswith(extn):
            file_name = file_name.replace(extn, "")
    if isinstance(file_path, str):
        return file_name
    elif isinstance(file_path, pathlib.Path):
        return pathlib.Path(file_name)
    

def remove_mmstack(file_path: str | pathlib.Path) -> str | pathlib.Path:
    """
    removes "MMStack_" substring from Micro-Manager image filenames.

    If file_path is a str, returns str with "MMStack_" removed. If file_path 
    is a pathlib.Path, instead returns pathlib.Path with "MMStack_" removed.
    """
    file_name = str(file_path).replace(f"_{FileSubtype.MMSTACK.value}", "")
    if isinstance(file_path, str):
        return file_name
    elif isinstance(file_path, pathlib.Path):
        return pathlib.Path(file_name)


def shutil_copy_ignore_images(root_dir: str | pathlib.Path, dest_dir: str | pathlib.Path):
    """
    Copies directory tree of root_dir, which includes all folders, subfolders,
    and files within those locations other than PNG and TIF files to dest_dir.

    ## Parameters:

    root_dir: str
        root directory that wants to be copied
    
    dest_dir: str
        destination directory that root_dir structure is copied to.
    """
    #*{file_extension} references all files with the given extension in a 
    #directory, so list below creates the ignore pattern to all image file 
    #types set in ImageFileType.
    #* to unpack list into arguments
    ignore_list = [f"*{extn}" for extn in get_image_extns()]
    ignore_pattern = shutil.ignore_patterns(*ignore_list)
    return shutil.copytree(
        root_dir, dest_dir, ignore=ignore_pattern, dirs_exist_ok=True)


def file_in_use(file_path: str | pathlib.Path) -> bool:
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
    

def get_batch_dest_path(source_path: str | pathlib.Path, 
                        dest_dir: str | pathlib.Path, 
                        prefix = "", 
                        suffix = ""
    ) -> pathlib.Path:
    """
    Creates pathlib.pathlib.Path object with root dest_dir and new subdirectory with
    name created from directory name of source_path with provided prefix and 
    suffix.

    ### Example:
    >>> get_batch_dest_path("C:/Jonah/foo", "D:/Drake", "lp_", "_dr")
    >>> 'D:/Drake/lp_foo_dr'
    """
    old_folder_name = get_dir_name(source_path)
    new_folder_name = f"{prefix}{old_folder_name}{suffix}"
    return pathlib.Path(dest_dir).joinpath(new_folder_name)


def get_save_path(file_path: pathlib.Path, 
                  source_path: pathlib.Path, 
                  dest_path: pathlib.Path,
                  file_name_end: str = ""
                  ) -> pathlib.Path:
    """
    Returns save path for use in batch processes. 
    """
    rel_path = file_path.relative_to(source_path)
    save_path = dest_path.joinpath(rel_path)
    save_path = remove_mmstack(save_path)
    save_path = remove_image_extn(save_path)
    extn = get_file_extn(file_path)
    new_file_end = f"{file_name_end}{extn}" 
    return pathlib.Path(f"{save_path}{new_file_end}")
    

def is_other_image_files(file_path: str | pathlib.Path) -> bool:
    """
    If there are other image files in the parent directory of file_path 
    (according to image file types in ImageFileType class), returns True. 
    Else, returns False.
    """
    file_path = pathlib.Path(file_path)
    for file in file_path.parent.iterdir():
        is_file_path = file_path.samefile(file)
        if get_file_type(file) in ImageFileType and not is_file_path:
            return True
    return False


def get_image_files_in_dir(dir: str | pathlib.Path) -> list[str | pathlib.Path]:
    """
    Returns list of all image files (according to image file types in
    ImageFileType class) in given directory.
    """
    dir_path = pathlib.Path(dir)
    files = []
    for file in dir_path.iterdir():
        with contextlib.suppress(TypeError):
            if get_file_type(file) in ImageFileType:
                files.append(str(file))
    #natsorted() sorts list so that files are sorted by number subscripts in
    #the correct order. ie, if there are 20 files named "image_1", "image_2",
    #..., order is "image_1", "image_2", ... "image_19" instead of "image_1",
    #"image_10", "image_11", ... "image_2", "image_3", ...
    files = natsorted(files)
    if isinstance(dir, pathlib.Path):
        files = [pathlib.Path(file) for file in files]
    return files


def get_file_extn(file_path: str | pathlib.Path) -> str:
    """
    Returns file extension as string.
    """
    return f".{str(file_path).split('.')[-1]}"


def read_images(file_path: str | pathlib.Path) -> np.ndarray:
    """
    reads in images in file and returns them as ndarray.

    This is mostly here because tifffile loads in all images from all image 
    files that share metadata, which hogs memory. If file_path is a tif file,
    this loads in only the images stored in that file.
    """
    if get_file_type(file_path) == ImageFileType.TIF:
        stack = TiffFile(file_path)
        num_pages = len(stack.pages)
        image = stack.asarray(range(num_pages))
    else:
        image = skimage.io.imread(file_path)
    return image
