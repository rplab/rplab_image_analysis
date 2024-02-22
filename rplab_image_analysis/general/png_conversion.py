import pathlib
from functools import partial
from multiprocessing import Pool

import psutil
from tifffile import TiffFile

from rplab_image_analysis.utils import files, metadata, file_types


PNG = file_types.ImageFileType.PNG.value[0]
PNGS = "_pngs"


def png_convert_batch(source_dir: str | pathlib.Path, 
                      dest_dir: str | pathlib.Path
                      ) -> str:
    """
    Converts all images in source_dir and all subdirectories to PNGs
    in dest_dir. Also copies over directory structure of source_dir and copies 
    over non-image files.

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
    dest_path = files.get_batch_path(source_path, dest_dir, PNGS)
    files.copytree_ignore_images(source_path, dest_path)
    dirs = files.yield_roots(source_path)
    _start_process(source_path, dest_path, dirs)
    return str(dest_path)


def convert_tif_to_png(file_path: str | pathlib.Path,
                       save_dir: str | pathlib.Path
                       ) -> str:
    """
    Converts tif image or stack to PNG(s).

    ### Parameters:

    file_path: str
        file path of image file.

    save_dir: str
        directory for images to be saved to. If directory does not exist,
        will be created.
    """
    file_path = pathlib.Path(file_path)
    save_dir = pathlib.Path(save_dir)
    save_dir.mkdir(exist_ok=True)
    files.copy_non_image_files(file_path.parent, save_dir)
    save_path = save_dir.joinpath(file_path.name)
    _convert_tif(file_path, save_path)


def _start_process(source_path: pathlib.Path, 
                        dest_path: pathlib.Path, 
                        dirs: list[pathlib.Path]):
    """
    Starts multiprocess to utilize full CPU when performing PNG conversion.
    """
    num_cores = psutil.cpu_count(logical=False)
    with Pool(num_cores) as pool:
        pool_func = partial(_png_conversion_task, source_path, dest_path)
        #imap used to do lazy loading of dirs so we aren't taking up a ton of
        #memory with a list of strings. Also, calling just imap() doesn't seem
        #to start processing pool. Iterating works fine, though there may be
        #side effects of this.
        for result in pool.imap(pool_func, dirs):
            pass


def _png_conversion_task(source_path: pathlib.Path, 
                         dest_path: pathlib.Path, 
                         dir: pathlib.Path
                         ):
    """
    Iterative task used by "worker threads" to convert images to PNGs.
    """
    for image_file in files.get_image_files(dir):
        save_path = files.get_save_path(image_file, source_path, dest_path)
        if file_types.is_tif(image_file):
            _convert_tif(image_file, save_path)
        else:
            image = files.read_image(image_file)
            files.save_image(save_path.with_suffix(PNG), image)


def _convert_tif(file_path: pathlib.Path, save_path: pathlib.Path):
    """
    Converts tif to PNG(s).
    """
    if metadata.is_mm(file_path):
        _convert_mm_tif(file_path, save_path)
    else:
        _convert_misc_tif(file_path, save_path)


def _convert_mm_tif(file_path: pathlib.Path, save_path: pathlib.Path):
    """
    converts tif with MM metadata.
    """
    try:
        meta = metadata.MMMetadata(file_path)
    except FileNotFoundError:
        _convert_misc_tif(file_path)
    else:
        pages = TiffFile(file_path).pages
        #first filename in metadata is what will be used for all files that 
        #share the metadata
        filename = meta.all_filenames[0]
        page_num = meta.get_filename_start_num(file_path.name)
        for page in pages:
            save_path = save_path.with_name(filename)
            if coords := meta.get_image_metadata(page_num).get_coords_str():
                save_path = save_path.with_stem(f"{save_path.stem}_{coords}")
            save_path = save_path.with_suffix(PNG)
            files.save_image(save_path, page.asarray())
            page_num += 1


def _convert_misc_tif(file_path: pathlib.Path, save_path: pathlib.Path):
    """
    converts tif without MM metadata.
    """
    pages = TiffFile(file_path).pages
    for page_num, page in enumerate(pages):
        if coords := f"{page_num + 1}" if page_num else "":
            save_path = save_path.with_stem(f"{save_path.stem}_{coords}")
        save_path = save_path.with_suffix(PNG)
        files.save_image(save_path, page.asarray())
