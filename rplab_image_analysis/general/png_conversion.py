import os
import numpy as np
import pathlib
import psutil
import skimage.io
import utils.files as files
from functools import partial
from multiprocessing import Pool
from tifffile import TiffFile
from utils.metadata import MMMetadata


PNG = files.ImageFileType.PNG.value[0]


def batch_convert_to_pngs(source_dir: str | pathlib.Path, 
                          dest_dir: str | pathlib.Path
                          ) -> str:
    source_path = pathlib.Path(source_dir)
    dest_path = files.get_batch_dest_path(source_path, dest_dir, 
                                          suffix = "_pngs")
    dirs = []
    for root, directories, filenames in os.walk(source_dir):
        for filename in filenames:
            dirs.append(root)
    dirs = set(dirs)
    if len(dirs) != 0:
        files.shutil_copy_ignore_images(source_path, dest_path)
        _start_multiprocess(source_path, dest_path, dirs)
    return str(dest_path)      


def _start_multiprocess(source_path: pathlib.Path, 
                        dest_path: pathlib.Path, 
                        dirs: list[pathlib.Path]):
    """
    Starts multiprocess to utilize full CPU when performing PNG conversion.
    """
    with Pool(psutil.cpu_count(logical=False)) as pool:
        pool_func = partial(
            _png_conversion_task, source_path, dest_path)
        pool.map(pool_func, dirs)


def _png_conversion_task(source_path: pathlib.Path, 
                         dest_path: pathlib.Path, 
                         dir: pathlib.Path):
    file_paths = files.get_image_files_in_dir(dir)
    if files.get_file_type(file_paths[0]) == files.ImageFileType.TIF:
        _tif_png_conversion_task(file_paths, dest_path, source_path)


def _tif_png_conversion_task(file_paths: list[pathlib.Path], 
                             dest_path: pathlib.Path, 
                             source_path: pathlib.Path):
    #keep track of page_num outside of file loop in case there are multiple 
    #tif files in a single directory.
    first_path = file_paths[0]
    page_num = 0
    for file_path in file_paths:
        stack = TiffFile(file_path)
        is_single_image = _get_stack_num_dims(stack) == 2
        if is_single_image:
            save_path = _get_single_save_path(
                file_path, source_path, dest_path)
            image = stack.asarray()
            _write_png(save_path, image)
        else:
            for page in stack.pages:
                save_path = _get_stack_save_path(
                    first_path, source_path, dest_path, page_num)
                image = page.asarray()
                _write_png(save_path, image)
                page_num += 1


def _get_stack_num_dims(stack: TiffFile):
    return len(stack.series[0].shape)


def _get_single_save_path(file_path: pathlib.Path, 
                          source_path: pathlib.Path, 
                          dest_path: pathlib.Path
                          ) -> pathlib.Path:
    new_name = _get_single_image_name(file_path)
    rel_path = _get_rel_path(source_path, file_path, new_name)
    return dest_path.joinpath(rel_path)


def _get_single_image_name(file_path: pathlib.Path) -> str:
    old_name = file_path.name
    new_name = files.remove_mmstack(old_name)
    new_name = files.remove_image_extn(old_name)
    return new_name


def _get_rel_path(source_path: pathlib.Path, 
                  file_path: pathlib.Path, 
                  new_name: str
                  ) -> pathlib.Path:
    old_name = file_path.name
    rel_path = file_path.relative_to(source_path)
    return pathlib.Path(str(rel_path).replace(old_name, new_name))


def _get_stack_save_path(file_path: pathlib.Path, 
                         source_path: pathlib.Path, 
                         dest_path: pathlib.Path, 
                         page_num: int
                         ) -> pathlib.Path:
    new_name = _get_stack_image_name(file_path, page_num)
    rel_path = _get_rel_path(source_path, file_path, new_name)
    return dest_path.joinpath(rel_path)


def _get_stack_image_name(file_path: pathlib.Path, page_num: int) -> str:
    name = file_path.name
    name = files.remove_mmstack(name)
    name = files.remove_image_extn(name)
    metadata = MMMetadata(file_path).get_image_metadata(page_num)
    coords = metadata.get_coords_str()
    return f"{name}_{coords}{PNG}"


def _write_png(save_path: pathlib.Path, image: np.ndarray):
    if not save_path.exists():
        skimage.io.imsave(
            fname=save_path, arr=image, check_contrast=False, plugin='imageio', 
            compress_level=3)
    