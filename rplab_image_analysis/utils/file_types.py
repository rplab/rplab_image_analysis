"""
This module contains functions classes and functions that are dirtectly related
to file types. This includes file type enum classes and functions that
determine the file type of a file.
"""


import pathlib

from enum import Enum

from rplab_image_analysis.utils import metadata



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
    OME: str = ".ome"


def get_file_type(file_path: str | pathlib.Path) -> ImageFileType:
    """
    Gets file type, determined by file extension.

    ### Paramaters:

    file_path: str

    ### Returns:

    file_type: FileType
        file type of file at file_path.
    """
    file_path = pathlib.Path(file_path)
    file_extn = file_path.suffix
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
    file_path = pathlib.Path(file_path)
    file_type = get_file_type(file_path)
    filename = file_path.name
    if file_type == ImageFileType.TIF and FileSubtype.MMSTACK.value in filename:
        return FileSubtype.MMSTACK
    if file_type == OtherFileType.TXT:
        if FileSubtype.METADATA.value in filename:
            return FileSubtype.METADATA
        elif FileSubtype.LS_NOTES.value in filename:
            return FileSubtype.LS_NOTES
        

def get_image_extns() -> list:
    """
    Returns list with all image file extensions.
    """
    extn_lists = [extn.value for extn in ImageFileType]
    return [extn for ftype in extn_lists for extn in ftype]


def is_image(file_path: str | pathlib.Path) -> bool:
    """
    If file is an image file according to file extensions in ImageFileType
    class, returns True. Else, returns False.
    """
    file_path = pathlib.Path(file_path)
    if file_path.suffix in get_image_extns():
        return True
    else:
        return False
    

def is_ls_pycro_notes(file_path: str | pathlib.Path):
    """
    If file_path is an ls_pycro_notes file, returns True.
    """
    return get_file_subtype(file_path) == FileSubtype.LS_NOTES
    

def is_mm(file_path: str | pathlib.Path) -> bool:
    """
    If file_path is a tif with MM metadata, returns true.
    """
    try:
        metadata.MMMetadata(file_path)
        return True
    except FileNotFoundError:
        return False


def is_mm_metadata(file_path: str | pathlib.Path):
    """
    If file_path is an MM metadata file, returns True.
    """
    return get_file_subtype(file_path) == FileSubtype.METADATA


def is_png(file_path: str | pathlib.Path):
    """
    If file_path is a PNG file, returns True.
    """
    return get_file_type(file_path) == ImageFileType.PNG


def is_tif(file_path: str | pathlib.Path):
    """
    If file_path is a tif file, returns True.
    """
    return get_file_type(file_path) == ImageFileType.TIF
