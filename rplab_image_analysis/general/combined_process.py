import pathlib

from rplab_image_analysis.utils import files, file_types
from rplab_image_analysis.general.background_subtraction import get_median_subtracted_image
from rplab_image_analysis.general.downsampling import get_downsampled_image

def combined_batch(source_dir: str,
                   dest_dir: str,
                   should_ds: bool = False,
                   should_ms: bool = False,
                   save_as_png: bool = True,
                   ds_factor: int = 1):
    source_path = pathlib.Path(source_dir)
    dest_path = pathlib.Path(dest_dir)
    stem = _get_combined_stem(should_ds, should_ms)
    for file in files.yield_walk_image_files(source_path):
        save_path = files.get_save_path(file, source_path, dest_path, stem)
        if save_as_png:
            save_path.with_suffix(file_types.ImageFileType.PNG.value[0])
        image = _combined_process(file, should_ds, should_ms, ds_factor)
        files.save_image(save_path, image)

def _combined_process(file_path, should_ds, should_ms, ds_factor):
    image = files.read_image(file_path)
    if should_ds:
        image = get_downsampled_image(image, ds_factor)
    if should_ms:
        image = get_median_subtracted_image(image)
    return image
        
def _get_combined_stem(should_ds, should_ms):
    stem = ""
    if should_ds:
        stem += "_ds"
    if should_ms:
        stem += "_ms"
    return stem
