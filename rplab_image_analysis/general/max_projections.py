import numpy as np
import skimage.io
from tifffile import TiffFile
from utils.files import get_file_type, FileType

def get_max_projection(file_path: str | list[str]) -> np.ndarray:
    """
    Creates max projection of images.

    ### Parameters:

    images: TiffFile | list[str]
        Images to be created into max projection. Should either be a 
        TiffFile class intance or a list of filepaths of images.
    
        If the images you want to create a max projection of are already arrays
        in python, just use numpy's max function.

    ### Returns:
        max_projection: np.ndarray
            max projection created from images.
    """
    if isinstance(file_path, str):
        file_type = get_file_type(file_path)
        if file_type == FileType.TIF:
            return _get_tif_max_projection(file_path)
        elif file_type == FileType.PNG:
            return skimage.io.imread(file_path)
    elif isinstance(file_path, list):
        return _get_multifile_max_projection(file_path)

def _get_tif_max_projection(file_path: str) -> np.ndarray:
    image_stack = TiffFile(file_path)
    for page_num, page in enumerate(image_stack.pages):
        image = page.asarray()
        if page_num == 0:
            max_projection = image
        else:
            max_projection = np.max(np.array([max_projection, image]), 0)
    return max_projection

def _get_multifile_max_projection(file_list: list) -> np.ndarray:
    for file_num, file in enumerate(file_list):
        file_type = get_file_type(file)
        if file_type == FileType.TIF:
            new_projection = _get_tif_max_projection(file)
            if file_num == 0:
                max_projection = new_projection
            else:
                max_projection = np.max(new_projection, max_projection, 0)
        elif file_type == FileType.PNG:
            image = skimage.io.imread(file)
            if file_num == 0:
                max_projection = image
            else:
                max_projection = np.max(np.array([max_projection, image]), 0)
    return max_projection