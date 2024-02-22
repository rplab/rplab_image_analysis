import pathlib

import numpy as np

from rplab_image_analysis.utils import files, metadata
import rplab_image_analysis.general.max_projections as max_projections


STITCHED = "_stitched"


def stitch_images(file_list: list[str | pathlib.Path],
                  save_path: str | pathlib.Path,
                  x_inverted: bool = False, 
                  y_inverted: bool = False,
                  swap_axes: bool = False
                  ):
    """
    Stitch images together. Currently only works with Micro-Manager images
    with stage positions in metadata.

    ### Parameters:

    file_list: list[str | pathlib.Path]
        list of image files to be stitched together
    
    save_path: str | pathlib.Path
        file path for image to be saved at. Should include filename and
        file extension.

    x_inverted: bool
        should be True if x stage positions should be inverted.

    y_inverted: bool
        should be True if y stage positions should be inverted.

    swap_axes: bool
        Swaps stages axes if True. Should be True for stitching images from the
        Willamette light sheet.
    """
    file_list = [pathlib.Path(file) for file in file_list]
    save_path = pathlib.Path(save_path)
    if metadata.is_mm(file_list[0]):
        for file in file_list:
            files.copy_non_image_files(file.parent, save_path.parent)
        stitched_image = _stitch_mm_images(
            file_list, x_inverted, y_inverted, swap_axes)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    files.save_image(save_path, stitched_image)


def stitch_ls_pycro(acq_dir: str,
                    save_dir: str,
                    fish_nums: list[int] = [],
                    image_types: list[str] = [],
                    channels: list[str] = [],
                    timepoints: list[int] = [],
                    x_inverted: bool = False, 
                    y_inverted: bool = False,
                    swap_axes: bool = False):
    """
    Batch creates stitched images from ls_pycro_app acquisition. acq_dir must
    be the "Acquisition" folder created by the acquisition.

    ### Parameters:

    acq_dir: str
        path to "Acquisition" directory of ls_pycro_app acquisition

    save_dir: str
        directory where images will be saved to.

    fish_nums: list[int] = []
        fish numbers that the user would like to stitch. If empty, all fish
        will be stitched.

    image_types: list[str] = []
        image types that the user would like to stitch. Possible arguments are
        "zstack", "video", "snap", "spectralvideo", and "spectralzstack".
        If empty, all will be stitched.

    channels: list[str] = []
        channels that the user would like to stitch. If empty, all channels
        will be stitched.

    timepoints: list[int] = []
        timepoints that the user would like to stitch. If empty, all timepoints
        will be stitched.

    x_inverted: bool
        should be True if x stage positions should be inverted.

    y_inverted: bool
        should be True if y stage positions should be inverted.

    swap_axes: bool
        Swaps stages axes if True. Should be True for stitching images from the
        Willamette light sheet.
    """
    acq_path = pathlib.Path(acq_dir)
    dest_path = pathlib.Path(save_dir).joinpath(f"{acq_path.stem}{STITCHED}")
    for fish_path in files.get_sorted_dirs(acq_path):
        fish = fish_path.name
        #fish will be "fish{num}" so to extract num, we take the characters
        #starting at index 4 to end.
        if fish_nums and int(fish[-1]) not in fish_nums:
            continue
        pos_paths = files.get_sorted_dirs(fish_path)
        rel_pos_paths = _get_rel_pos_paths(
            pos_paths, image_types, channels, timepoints)
        for rel_pos_path in rel_pos_paths:
            image_list = _get_ls_pycro_image_list(pos_paths, rel_pos_path)
            if image_list:
                save_path = files.get_save_path(
                    image_list[0], acq_path, dest_path)
                save_path = save_path.with_stem(f"{save_path.stem}{STITCHED}")
                stitch_images(
                    image_list, save_path, x_inverted, y_inverted, swap_axes)
    return str(dest_path)        


def _stitch_mm_images(file_list: list[pathlib.Path], 
                      x_inverted: bool, 
                      y_inverted: bool,
                      swap_axes: bool
                      ) -> np.ndarray:
    """
    Stitches images with micro-manager metadata. 
    """
    for file_num, file_path in enumerate(file_list):
        image_metadata = metadata.MMMetadata(file_path).get_image_metadata(0)
        new_image = _get_new_image(file_path)
        positions = _get_positions(image_metadata)
        if file_num == 0:
            start_positions = positions
            ds_factor = _get_ds_factor(image_metadata, new_image)
            image_dims = _init_image_dims(image_metadata, ds_factor)
            pixel_size = _get_pixel_size(image_metadata, ds_factor)
            x_range, y_range = _init_ranges(image_dims)
            stitched_image = new_image
        else:
            x_offset, y_offset = _get_xy_offsets(
                start_positions, positions, x_inverted, y_inverted, swap_axes, 
                pixel_size)
            stitched_image = _stitch_new_image(
                new_image, stitched_image, x_offset, y_offset, image_dims, 
                x_range, y_range)
    return stitched_image


def _get_new_image(file_path: pathlib.Path):
    file_list = files.get_image_files(file_path.parent)
    if metadata.from_same_mm_sequence(file_list):
        return max_projections._get_max_from_list(file_list)
    else:
        return max_projections.get_max(file_path)


def _get_positions(image_metadata: metadata.MMImageMetadata) -> tuple:
    """
    gets x and y stage positions according to image metadata and returns it
    as tuple.
    """
    return (image_metadata.x_pos, image_metadata.y_pos)


def _get_ds_factor(image_metadata: metadata.MMImageMetadata,
                   new_image: np.ndarray
                   ) -> int:
    """
    Gets downsample factor to be used in determining correct pixel size of 
    image.
    """
    image_height = _get_image_height(new_image)
    meta_height = image_metadata.image_height
    if image_height != meta_height:
        return int(meta_height/image_height)
    else:
        return 1
    

def _init_image_dims(image_metadata: metadata.MMImageMetadata, 
                     ds_factor: int
                     ) -> list[int]:
    meta_width = image_metadata.image_width
    meta_height = image_metadata.image_height
    return [int(meta_height/ds_factor), int(meta_width/ds_factor)]
    

def _get_image_height(image: np.ndarray) -> int:
    """
    returns height of image
    """
    return image.shape[-2]


def _get_pixel_size(image_metadata: metadata.MMImageMetadata, ds_factor: int):
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
                    x_inverted: bool,
                    y_inverted: bool,
                    swap_axes: bool,
                    pixel_size: float
                    ) -> tuple[int]:
    """
    Returns x and y pixel offets relative to the position of the first image
    added to the stitched image. 
    """
    x_offset = _get_pixel_offset(start_positions[0], positions[0], pixel_size)
    x_offset *= -1 if x_inverted else 1
    y_offset = _get_pixel_offset(start_positions[1], positions[1], pixel_size)
    y_offset *= -1 if y_inverted else 1
    if not swap_axes:
        return x_offset, y_offset
    return y_offset, x_offset


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
    new_x_range, new_y_range = _get_new_ranges(x_offset, y_offset, image_dims)
    x_extns, y_extns = _get_stitched_extns(
        stitched_x_range, stitched_y_range, new_x_range, new_y_range)
    stitched_x_range, stitched_y_range = _update_stitched_range(
        stitched_x_range, stitched_y_range, new_x_range, new_y_range)
    
    stitched_image = _add_stitched_extns(stitched_image, x_extns, y_extns)
    slices = _get_position_slices(x_extns, y_extns, image_dims)
    new_region = _get_new_region_max(new_image, stitched_image, slices)
    stitched_image[slices[1], slices[0]] = new_region
    return stitched_image


def _get_new_ranges(x_stage_offset: int, 
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


def _get_stitched_extns(stitched_x_range: list[int], 
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


def _add_stitched_extns(stitched_image: np.ndarray, 
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
        stitched_image = np.concatenate([left_extension, 
                                         stitched_image], 
                                         axis=1)
    if x_extensions[1] > 0:
        right_extension = np.zeros([stitched_image.shape[0], x_extensions[1]])
        stitched_image = np.concatenate([stitched_image, 
                                         right_extension], 
                                         axis=1)
    if y_extensions[0] > 0:
        top_extension = np.zeros([y_extensions[0], stitched_image.shape[1]])
        stitched_image = np.concatenate([top_extension, 
                                         stitched_image])
    if y_extensions[1] > 0:
        bot_extension = np.zeros([y_extensions[1], stitched_image.shape[1]])
        stitched_image = np.concatenate([stitched_image, 
                                         bot_extension])

    #numpy concatenation doesn't seem to conserve datatype, so ensure
    #datatype is same as original stitched image.
    return stitched_image.astype(dtype)


def _get_position_slices(x_extensions: list[int], 
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


def _get_new_region_max(new_image, stitched_image, slices):
    """
    Takes region of stitched image where new_image will be stitched
    and then returns max projection of region and new_image.
    """
    #If two images are added with the same stage position (ie, if z-stack 
    #is split into two files because it's too large for one), second region
    #would just overwrite the first. This takes a max projection of the
    #newly added region and the previously added one so this doesn't 
    #happen.
    stitched_region = stitched_image[slices[1], slices[0]]
    region_array = np.array((stitched_region, new_image))
    return np.max(region_array, 0)


def _get_rel_pos_paths(pos_paths: list[pathlib.Path],
                       image_types: list[str] = [],
                       channels: list[str] = [],
                       timepoints: list[int] = []
                       ) -> list[pathlib.Path]:
    """
    Returns paths to image directories relative to position directories.
    For example, a rel_pos_path may be pathlib.Path object with the path
    "zstack/GFP/timepoint1" or "zstack/RFP/timepoint12".

    rel_pos_paths is just a list of all these relative paths that exist in the
    acquisition folder directory.
    """
    rel_pos_paths = []
    for pos_path in pos_paths:
        for image_type_path in files.get_sorted_dirs(pos_path):
            image_type = image_type_path.name
            if image_types and image_type_path.name not in image_types:
                continue
            for channel_path in files.get_sorted_dirs(image_type_path):
                channel = channel_path.name
                if channels and channel_path.name not in channels:
                    continue
                for tp_path in files.get_sorted_dirs(channel_path):
                    timepoint = tp_path.name
                    #timepoint will be "timepoint{num}" so to extract num,
                    #we take the characters starting at index 9 to end.
                    if timepoints and int(timepoint[9:]) not in timepoints:
                        continue
                    rel_image_type_path = pathlib.Path(image_type)
                    rel_channel_path = rel_image_type_path.joinpath(channel)
                    rel_pos_path = rel_channel_path.joinpath(timepoint)
                    if rel_pos_path not in rel_pos_paths:
                        rel_pos_paths.append(rel_pos_path)
    return rel_pos_paths


def _get_ls_pycro_image_list(pos_paths: list[pathlib.Path], 
                             rel_pos_path: pathlib.Path
                             ) -> list[pathlib.Path]:
    """
    Iterates through true position paths in acquisition and checks if relative 
    path created by pos_path.joinpath(rel_pos_path) exists. If it does, it is 
    appended to a list, which is then returned.
    """
    image_list = []
    for pos_path in pos_paths:
        stitch_pos_path = pos_path.joinpath(rel_pos_path)
        if stitch_pos_path.exists():
            image_path = files.get_image_files(stitch_pos_path)[0]
            image_list.append(image_path)
    return image_list
