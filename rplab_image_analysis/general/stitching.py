import pathlib
import numpy as np
import skimage
import skimage.io
from general import get_max_projection
from utils.metadata import MMMetadata, MMImageMetadata, is_micro_manager


def stitch_images(file_list: str,
                  save_path: str,
                  pixel_size: int = 0.1625,
                  x_stage_is_inverted: bool = False,
                  y_stage_is_inverted: bool = False,
                  num_90_rotations: int = 0):
    """
    Stitch images together. Currently only works with Micro-Manager images
    with stage positions in metadata.

    ### Parameters:

    file_list: list[str]
        list of image files to be stitched together
    
    save_path: str
        file path for image to be saved at. Should include filename. Current
        supported file types to be saved as are tif and png.

    pixel_size: float = 0.1625
        pixel size in microns per pixel. Default value is for 6.5um camera 
        sensor pixel size and 40x objective.

    is_x_stage_inverted: bool = False
        Should be set True if the sample moving right is a negative x-stage
        position change. Else, should be set to False.

    is_y_stage_inverted: bool = False
        Should be set True if the sample moving up is a negative y-stage
        position change. Else, should be set to False.

    num_90_rotations: int = 0
        number of 90 degree rotations to be applied to images. Relevant
        because xy axes of camera may not line up with xy axes of stage. 
        For Klamath, this should be 0, whereas for Willamette, it should be 3.
    """
    file_list = [pathlib.Path(file) for file in file_list]
    save_path = pathlib.Path(save_path)
    if is_micro_manager(file_list[0]):
        stitched_image = _stitch_mm_images(
            file_list, pixel_size, x_stage_is_inverted, y_stage_is_inverted, 
            num_90_rotations)
    skimage.io.imsave(save_path, stitched_image, check_contrast=False)


def _stitch_mm_images(file_list: list[pathlib.Path], 
                      pixel_size: float, 
                      x_stage_is_inverted: bool, 
                      y_stage_is_inverted: bool, 
                      num_90_rotations: int
                      ) -> np.ndarray:
    """
    Stitches images with micro-manager metadata. 
    """
    inversion = (x_stage_is_inverted, y_stage_is_inverted)
    for region_num, file_path in enumerate(file_list):
        image_metadata = MMMetadata(file_path).get_image_metadata(0)
        meta_dims = _get_meta_dims(image_metadata)
        new_image = _get_new_image(file_path, num_90_rotations, meta_dims)
        positions = _get_positions(image_metadata)

        if region_num == 0:
            start_positions = positions
            ds_factor = _get_ds_factor(new_image, meta_dims)
            pixel_size = _get_pixel_size(image_metadata, ds_factor)
            stitched_x_range, stitched_y_range = _init_ranges(meta_dims)
            stitched_image = new_image
        else:
            x_offset, y_offset = _get_xy_offsets(
                start_positions, positions, inversion, pixel_size)
            stitched_image = _stitch_new_image(
                new_image, stitched_image, x_offset, y_offset, meta_dims, 
                stitched_x_range, stitched_y_range)
    return stitched_image


def _get_meta_dims(image_metadata: MMImageMetadata) -> list[int]:
    """
    gets image height and width and returns it as list.
    """
    #[height, width] to stay consistent with array dimensions order
    return [image_metadata.image_height, image_metadata.image_width]


def _get_new_image(file_path: pathlib.Path, 
                   num_90_rotations: int, 
                   image_dims: list[int]
                   ) -> np.ndarray:
    """
    Creates maximum projection of images in image_file, rotates image according
    to num_90_rotations, and then returns max projection as ndarray.
    """
    new_image = get_max_projection(file_path)
    if num_90_rotations != 0:
        new_image = np.rot90(new_image, k=num_90_rotations)
        _rotate_image_dims(image_dims, num_90_rotations)
    return new_image


def _rotate_image_dims(image_dims: list, num_90_rotations: int):
    """
    Swaps image dims according to rotation of image.
    """
    if num_90_rotations % 2 == 1:
        image_dims[1], image_dims[0] = image_dims[0], image_dims[1]


def _get_positions(image_metadata: MMImageMetadata) -> tuple:
    """
    gets x and y stage positions according to image metadata and returns it
    as tuple.
    """
    return (image_metadata.x_pos, image_metadata.y_pos)


def _get_ds_factor(stitched_image: np.ndarray, image_dims: list[int]) -> int:
    """
    Gets downsample factor to be used in determining correct pixel size of 
    image.
    """
    image_height = _get_image_height(stitched_image)
    meta_height = image_dims[0]
    if image_height != meta_height:
        return int(meta_height/image_height)
    else:
        return 1
    

def _get_image_height(image: np.ndarray) -> int:
    """
    returns height of image
    """
    return image.shape[-2]


def _get_pixel_size(image_metadata: MMImageMetadata, ds_factor: int):
    """
    returns pixel size calculated from pixel size in metadata, binning, and
    downsample factor.
    """
    return image_metadata.pixel_size*image_metadata.binning*ds_factor


def _init_ranges(image_dims: list[int]) -> tuple[list]:
    """
    Initializes x and y ranges to be used in dynamic resizing of stitched
    image.
    """
    stitched_x_range = [0, image_dims[1]]
    stitched_y_range = [0, image_dims[0]]
    return stitched_x_range, stitched_y_range


def _get_xy_offsets(start_positions: list[int], 
                    positions: list[int], 
                    inversion: list[bool], 
                    pixel_size: float
                    ) -> tuple[int]:
    """
    Returns x and y pixel offets relative to the position of the first image
    added to the stitched image. 
    """
    x_offset = _get_pixel_offset(start_positions[0], positions[0], pixel_size)
    x_offset *= -1 if inversion[0] else 1
    y_offset = _get_pixel_offset(start_positions[1], positions[1], pixel_size)
    y_offset *= -1 if inversion[1] else 1
    return x_offset, y_offset


def _get_pixel_offset(start_um: float, 
                      end_um: float, 
                      pixel_size: float
                      ) -> int:
    """
    Calculates pixel offset between images based on difference in 
    stage positions and returns it.
    """
    return round((end_um - start_um)/pixel_size)


def _stitch_new_image(new_image: np.ndarray, 
                      stitched_image: np.ndarray, 
                      x_offset: int, 
                      y_offset: int, 
                      image_dims: list[int], 
                      stitched_x_range: list[int], 
                      stitched_y_range: list[int]
                      ) -> np.ndarray:
    """
    Stitches new_image with stitched_image based on stage positions in
    Micro-Manager metadata.
    """
    new_x_range, new_y_range = _get_new_image_range(
        x_offset, y_offset, image_dims)
    x_extensions, y_extensions = _get_stitched_extensions(
        stitched_x_range, stitched_y_range, new_x_range, new_y_range)
    stitched_x_range, stitched_y_range = _update_stitched_range(
        stitched_x_range, stitched_y_range, new_x_range, new_y_range)
    
    stitched_image = _add_stitched_extensions(
        stitched_image, x_extensions, y_extensions)
    slices = _get_new_image_position_slices(
        x_extensions, y_extensions, image_dims)
    #If two images are added with the same stage position (ie, if z-stack 
    # is split into two files because it's too large for one), second region
    #would just overwrite the first. This takes a max projection of the
    #newly added region and the previously added one so this doesn't 
    #happen.
    stitched_region = stitched_image[slices[1], slices[0]]
    region_array = np.array((stitched_region, new_image))
    new_region = np.max(region_array, 0)
    stitched_image[slices[1], slices[0]] = new_region
    return stitched_image


def _get_new_image_range(x_stage_offset: int, 
                         y_stage_offset: int, 
                         image_dims: list[int, int]
                         ) -> tuple[list[int], list[int]]:
    """
    Gets min and max pixel positions of new_image based on x_stage_offset,
    y_stage_offset, and width and height of new_image.
    """
    new_x_range = [x_stage_offset, x_stage_offset + image_dims[1]]
    new_y_range = [y_stage_offset, y_stage_offset + image_dims[0]]
    return new_x_range, new_y_range


def _get_stitched_extensions(stitched_x_range: list[int], 
                             stitched_y_range: list[int], 
                             new_image_x_range: list[int], 
                             new_image_y_range: list[int]
                             ) -> tuple[list[int]]:
    """
    Gets stitched extensions--number of rows and columns to be concatenated
    to stitched_image--to make room for new_image to be added.
    """
    x_min_extension = stitched_x_range[0] - new_image_x_range[0]
    x_max_extension = new_image_x_range[1] - stitched_x_range[1]
    y_min_extension = stitched_y_range[0] - new_image_y_range[0]
    y_max_extension = new_image_y_range[1] - stitched_y_range[1]
    x_extensions = [x_min_extension, x_max_extension]
    y_extensions = [y_min_extension, y_max_extension]
    return x_extensions, y_extensions


def _update_stitched_range(stitched_x_range: list[int], 
                           stitched_y_range: list[int], 
                           new_x_range: list[int], 
                           new_y_range: list[int]
                           ) -> tuple[list[int]]:
    """
    Determines new stitched image range by comparing min and max values of
    old stitched image range and new image range.
    """
    
    stitched_x_range[0] = min(stitched_x_range[0], new_x_range[0])
    stitched_y_range[0] = min(stitched_y_range[0], new_y_range[0])
    stitched_x_range[1] = max(stitched_x_range[1], new_x_range[1])
    stitched_y_range[1] = max(stitched_y_range[1], new_y_range[1])
    return stitched_x_range, stitched_y_range


def _add_stitched_extensions(stitched_image: np.ndarray, 
                             x_extensions: list[int], 
                             y_extensions: list[int]
                             ) -> np.ndarray:
    """
    Concatenates image extensions and stitched image. Image extensions
    are arrays of zeros that are added to the left, right, top, and bottom
    of stitched_image to make space for newly added new_image.
    """
    dtype = stitched_image.dtype
    if x_extensions[0] > 0:
        extension = np.zeros([stitched_image.shape[0], x_extensions[0]])
        stitched_image = np.c_[extension, stitched_image]
    if x_extensions[1] > 0:
        extension = np.zeros([stitched_image.shape[0], x_extensions[1]])
        stitched_image = np.c_[stitched_image, extension]
    if y_extensions[0] > 0:
        extension = np.zeros([y_extensions[0], stitched_image.shape[1]])
        stitched_image = np.concatenate([extension, stitched_image])
    if y_extensions[1] > 0:
        extension = np.zeros([y_extensions[1], stitched_image.shape[1]])
        stitched_image = np.concatenate([stitched_image, extension])

    #numpy concatenation doesn't seem to conserve datatype, so ensure
    #datatype is same as original stitched image.
    return stitched_image.astype(dtype)


def _get_new_image_position_slices(x_extensions: list[int], 
                                   y_extensions: list[int], 
                                   image_dims: list[int]
                                   ) -> tuple[slice, slice]:
    """
    Gets image position slices where new_image will be inserted
    into stitched_image array.
    """
    if x_extensions[0] > 0:
        x_slice = slice(0, image_dims[1])
    else:
        x_slice = slice(-x_extensions[0], image_dims[1] - x_extensions[0])

    if y_extensions[0] > 0:
        y_slice = slice(0, image_dims[0])
    else:
        y_slice = slice(-y_extensions[0], image_dims[0] - y_extensions[0])
    return x_slice, y_slice
