import pathlib
import numpy as np
import skimage
import skimage.io
import tifffile

import rplab_image_analysis.utils.metadata as metadata
from rplab_image_analysis.general.max_projections import get_max_projection


def stitch_images(file_list: str,
                  save_path: str,
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
    if metadata.is_micro_manager(file_list[0]):
        stitched_image = _stitch_mm_images(
            file_list, x_stage_is_inverted, y_stage_is_inverted, 
            num_90_rotations)
    skimage.io.imsave(save_path, stitched_image, check_contrast=False)


def _stitch_mm_images(file_list: list[pathlib.Path], 
                      x_stage_is_inverted: bool, 
                      y_stage_is_inverted: bool, 
                      num_90_rotations: int
                      ) -> np.ndarray:
    """
    Stitches images with micro-manager metadata. 
    """
    inversion = (x_stage_is_inverted, y_stage_is_inverted)
    if len(file_list) > 1:
        stitched_image = _stitch_multi_file_mm(file_list, num_90_rotations, inversion)
    else:
        stitched_image = _stitch_multi_region_mm(file_list[0], num_90_rotations, inversion)
    return stitched_image


def _stitch_multi_file_mm(file_list, num_90_rotations, inversion):
    for file_num, file_path in enumerate(file_list):
        new_image = get_max_projection(file_path)
        image_metadata = metadata.MMMetadata(file_path).get_image_metadata(0)
        position = _get_position(image_metadata)
        if file_num == 0:
            start_position = position
            ds_factor = _get_ds_factor(new_image.shape[-2], image_metadata.image_height)
            pixel_size = _get_pixel_size(image_metadata.pixel_size, ds_factor)
            stitched_image = np.rot90(new_image, num_90_rotations)
            x_offset_range, y_offset_range = _get_start_ranges(stitched_image.shape[-1], stitched_image.shape[-2], num_90_rotations)
        else:
            new_image = np.rot90(new_image, num_90_rotations)
            x_offset, y_offset = _get_xy_offsets(
                start_position, position, inversion, pixel_size)
            stitched_image = _stitch_new_image(
                new_image, stitched_image, x_offset, y_offset, 
                x_offset_range, y_offset_range)
    return stitched_image
            

def _stitch_multi_region_mm(file, num_90_rotations, inversion):
    meta = metadata.MMMetadata(file)
    for page_num, page in enumerate(tifffile.TiffFile(file).pages):
        new_image = page.asarray()
        image_metadata = meta.get_image_metadata(page_num)
        position = _get_position(image_metadata)
        if page_num == 0:
            start_position = position
            ds_factor = _get_ds_factor(new_image.shape[-2], image_metadata.image_height)
            pixel_size = _get_pixel_size(image_metadata.pixel_size, ds_factor)
            stitched_image = np.rot90(new_image, num_90_rotations)
            x_offset_range, y_offset_range = _get_start_ranges(image_metadata)
        else:
            new_image = np.rot90(new_image, num_90_rotations)
            x_offset, y_offset = _get_xy_offsets(
                start_position, position, inversion, pixel_size)
            stitched_image = _stitch_new_image(
                new_image, stitched_image, x_offset, y_offset, 
                x_offset_range, y_offset_range)
    return stitched_image


def _get_ds_factor(image_height: np.ndarray, meta_height: int) -> int:
    """
    Gets downsample factor to be used in determining correct pixel size of 
    image.
    """
    return int(meta_height/image_height)


def _get_pixel_size(meta_pixel_size: float, ds_factor: float):
    return meta_pixel_size*ds_factor


def _get_position(image_metadata: metadata.MMImageMetadata):
    return (image_metadata.x_pos, image_metadata.y_pos)


def _get_start_ranges(image_width: int, 
                      image_height: int, 
                      num_90_rotations: int
                      ) -> tuple[list[int]]:
    """
    Initializes x and y ranges to be used in dynamic resizing of stitched
    image.
    """
    if num_90_rotations % 2 == 0:
        stitched_x_range = [0, image_width]
        stitched_y_range = [0, image_height]
    else:
        stitched_x_range = [0, image_width]
        stitched_y_range = [0, image_height]
    return stitched_x_range, stitched_y_range


def _get_xy_offsets(start_position: list[int], 
                    position: list[int], 
                    inversion: list[bool], 
                    pixel_size: float
                    ) -> tuple[int]:
    """
    Returns x and y pixel offets relative to the position of the first image
    added to the stitched image. 
    """
    x_offset = _get_pixel_offset(start_position[0], position[0], pixel_size)
    x_offset *= -1 if inversion[0] else 1
    y_offset = _get_pixel_offset(start_position[1], position[1], pixel_size)
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
                      x_offset_range: list[int], 
                      y_offset_range: list[int]
                      ) -> np.ndarray:
    """
    Stitches new_image with stitched_image based on stage positions in
    Micro-Manager metadata.
    """
    new_shape = new_image.shape
    x_extensions, y_extensions = _get_extension_nums(
        new_shape, x_offset, y_offset, x_offset_range, y_offset_range)
    x_offset_range, y_offset_range = _update_offset_range(
        new_shape, x_offset, y_offset, x_offset_range, y_offset_range)
    stitched_image = _add_stitched_extensions(
        stitched_image, x_extensions, y_extensions)
    slices = _get_new_image_slices(
        new_shape, x_extensions, y_extensions)
    stitched_image = _place_new_image(stitched_image, new_image, slices)
    return stitched_image


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
        left_extension = np.zeros([stitched_image.shape[0], x_extensions[0]])
        #The axis=1 argument concatentates on along the second (x) axis
        stitched_image = np.concatenate([left_extension, stitched_image], axis=1)
    if x_extensions[1] > 0:
        right_extension = np.zeros([stitched_image.shape[0], x_extensions[1]])
        stitched_image = np.concatenate([stitched_image, right_extension], axis=1)
    if y_extensions[0] > 0:
        top_extension = np.zeros([y_extensions[0], stitched_image.shape[1]])
        stitched_image = np.concatenate([top_extension, stitched_image])
    if y_extensions[1] > 0:
        bot_extension = np.zeros([y_extensions[1], stitched_image.shape[1]])
        stitched_image = np.concatenate([stitched_image, bot_extension])

    #numpy concatenation doesn't conserve datatype, so ensure
    #datatype is same as original stitched image.
    return stitched_image.astype(dtype)


def _get_extension_nums(new_shape: tuple[int],
                        x_offset: int,
                        y_offset: int,
                        x_offset_range: list[int],
                        y_offset_range: list[int]
                        ) -> tuple[list[int]]:
    """
    Gets stitched extensions--number of rows and columns to be concatenated
    to stitched_image--to make room for new_image to be added.

    x_extensions contains left and right extensions and y_extensions has
    top and bottom extensions.
    """
    x_min_extension = x_offset_range[0] - x_offset
    x_max_extension = (x_offset + new_shape[-2]) - x_offset_range[1]
    y_min_extension = y_offset_range[0] - y_offset
    y_max_extension = (y_offset + new_shape[-2]) - y_offset_range[1]
    x_extensions = [x_min_extension, x_max_extension]
    y_extensions = [y_min_extension, y_max_extension]
    return x_extensions, y_extensions


def _get_new_image_slices(new_shape: tuple[int], 
                          x_extensions: list[int], 
                          y_extensions: list[int],
                          ) -> tuple[slice]:
    """
    Gets image position slices where new_image will be inserted
    into stitched_image array.
    """
    #if extensions were added to left side of image to make room for
    #new image
    if x_extensions[0] > 0:
        x_slice = slice(0, new_shape[-1])
    #if x_extensions[0] <= 0 then no extensions were added, and so -extensions[0]
    #is the relativive offset from the left side of the image.
    else:
        x_slice = slice(-x_extensions[0], new_shape[-1] - x_extensions[0])
    #same idea as x except for from the top of the image.
    if y_extensions[0] > 0:
        y_slice = slice(0, new_shape[-2])
    else:
        y_slice = slice(-y_extensions[0], new_shape[-2] - y_extensions[0])
    return x_slice, y_slice


def _place_new_image(stitched_image: np.ndarray, 
                     new_image: np.ndarray, 
                     slices: tuple[slice]
                     ) -> np.ndarray:
    #If two images are added with the same stage position (ie, if z-stack 
    #is split into two files because it's too large for one), second region
    #would just overwrite the first. This takes a max projection of the
    #newly added region and the previously added one so this doesn't 
    #happen.
    #region of image where new image will be placed
    stitched_region = stitched_image[slices[1], slices[0]]
    #array containing both region of stitched image and new image to be added
    region_array = np.array((stitched_region, new_image))
    #creates new array with max values between the two arrays
    new_region = np.max(region_array, 0)
    #places new region into stitched image.
    stitched_image[slices[1], slices[0]] = new_region
    return stitched_image


def _update_offset_range(new_shape: tuple[int],
                         x_offset: int,
                         y_offset: int,
                         x_offset_range: list[int], 
                         y_offset_range: list[int],
                         ) -> tuple[list[int]]:
    """
    Determines new stitched image range by comparing min and max values of
    old stitched image range and offsets. If new image is added with offset
    within these new ranges, extensions will not have to be added.
    """
    x_offset_range[0] = min(x_offset_range[0], x_offset)
    y_offset_range[0] = min(y_offset_range[0], y_offset)
    x_offset_range[1] = max(x_offset_range[1], x_offset + new_shape[-1])
    y_offset_range[1] = max(y_offset_range[1], y_offset + new_shape[-2])
    return x_offset_range, y_offset_range
