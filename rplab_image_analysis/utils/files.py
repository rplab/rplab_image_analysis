import shutil
from enum import Enum

class FileType(Enum):
    """
    Enum class with constants representing file type, which is determined
    by file extension. 
    """
    TIF: str = ".tif"
    PNG: str = ".png"
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
def get_file_type(file_path: str) -> FileType:
    """
    Gets file type, determined by file extension.

    ### Paramaters:

    file_path: str

    ### Returns:

    file_type: FileType
        file type of file at file_path.
    """
    if file_path.endswith(FileType.TXT.value):
        return FileType.TXT
    elif file_path.endswith(FileType.TIF.value):
        return FileType.TIF
    elif file_path.endswith(FileType.PNG.value):
        return FileType.PNG

def get_file_subtype(file_path: str) -> FileSubtype:
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
    file_type = get_file_type(file_path)
    if file_type == FileType.TIF:
        if FileSubtype.OME.value in file_path:
            if FileSubtype.MMSTACK.value in file_path:
                return FileSubtype.MMSTACK
            else:
                return FileSubtype.OME
    if file_type == FileType.TXT:
        if FileSubtype.METADATA.value in file_path:
            return FileSubtype.METADATA
        elif FileSubtype.LS_NOTES.value in file_path:
            return FileSubtype.LS_NOTES

def shutil_copy_ignore_images(root_dir: str, dest_dir: str):
    """
    Copies directory tree of root_dir, which includes all folders, subfolders,
    and files within those locations other than PNG and TIF files to dest_dir.

    Parameters:

    root_dir: str
        root directory that wants to be copied
    
    dest_dir: str
        destination directory that root_dir structure is copied to.
    """
    tif_files = f"*.{FileType.TIF.value}"
    png_files = f"*.{FileType.PNG.value}"
    ignore_pattern = shutil.ignore_patterns(tif_files, png_files)
    shutil.copytree(root_dir, dest_dir, ignore=ignore_pattern)
    