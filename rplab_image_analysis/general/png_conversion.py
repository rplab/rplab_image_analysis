import os
import pathlib
import psutil
import shutil
import tifffile
from multiprocessing import Pool
from skimage import io
from tifffile import TiffFile

C = "channel"
P = "position"
Z = "z"
T = "time"

def png_conversion_task(file_path_tuple):
    root = file_path_tuple[0]
    filename = file_path_tuple[1]
    file_path = pathlib.Path(root).joinpath(filename).__str__()
    write_path = root.replace(folder_path, dest_path)
    filename_no_extension = filename.split(".")[0]

    stack = TiffFile(file_path)
    series = stack.series[0]
    is_micromanager = stack.pages[0].is_micromanager
    if is_micromanager:
        if len(series.shape)==2: #single images
            #increase compress level(0-9) to gain few percent better 
            #compression but much slower
            new_file_path = pathlib.Path(write_path).joinpath(
                f"{filename_no_extension}.png").__str__()
            io.imsave(fname=new_file_path, 
                    arr=stack.asarray(), 
                    check_contrast=False, 
                    plugin='imageio', 
                    compress_level=3)
        else: #image stacks
            for page_num, page in enumerate(stack.pages):
                coords_dict = get_coords_dict(series, page_num)
                new_file_name = get_new_file_name(
                    filename_no_extension, coords_dict)
                new_file_path = pathlib.Path(write_path).joinpath(
                    f"{new_file_name}.png").__str__()
                io.imsave(fname=new_file_path, 
                        arr=page.asarray(), 
                        check_contrast=False, 
                        plugin='imageio', 
                        compress_level=3)
        #shutil.rmtree() deletes dir and files where tif file was 
        #os.removedirs() removes the entire directory tree but only if it's 
        #completely empty.
        shutil.rmtree(root)
        os.removedirs(root)

def get_coords_dict(series: tifffile.TiffPageSeries, page_num: int) -> dict:
    """
    returns dictionary with image coords. ie if the image is from z-slice 21 
    and taken with channel 2, coords_dict will be {"Z": 20, "C": 1}
    """
    dimensions_dict = get_dimensions_dict(series)
    quotient = page_num
    coords_dict = {}
    for item in dimensions_dict.items():
        quotient, remainder = divmod(quotient, item[1])
        coords_dict[item[0]] = remainder
        if quotient == 0:
            break
    return coords_dict

def get_dimensions_dict(series: tifffile.TiffPageSeries) -> dict:
    #last two parts of shape are the image width and height. We only want 
    #the coords.
    coords = list(series.shape[:-2])
    #this grabs the letter tags of the grabbed coord values.
    axis_order = [axis for axis in series.axes[:len(coords)]]
    #reverse because axes are in reverse order of how images they are stored 
    #in tif stack.
    coords.reverse()
    axis_order.reverse()
    return dict(zip(axis_order, coords))

def get_new_file_name(filename_no_extension: str, coords_dict: dict) -> str:
    """
    Creates a new file name based on original name and coords in coords_dict.

    coords_dict: dict - dictionary that contains axes and coordinates for said 
    axis, ie if the image's axes are "CZ" and there are four channels and 8 
    z-slices, then coords_dict = {"C": 4, "Z": 8}.
    """
    if "C" in coords_dict.keys():
        channel_num = coords_dict['C']
    else:
        channel_num = 0
    if "P" in coords_dict.keys():
        position_num = coords_dict['P']
    else:
        position_num = 0
    if "T" in coords_dict.keys():
        time_num = coords_dict['T']
    else:
        time_num = 0
    if "Z" in coords_dict.keys():
        z_num = coords_dict['Z']
    else:
        z_num = 0
    return f"{filename_no_extension}_{C}{channel_num:03d}_{P}{position_num:03d}_{T}{time_num:03d}_{Z}{z_num:03d}"

def file_in_use(file_path):
    """
    Checks to see if file located at file_path is currently in use by process
    listed in psutil.processess_iter(). If file is in use, returns True. Else, False.
    """
    for process in psutil.process_iter():
        try:
            for item in process.open_files():
                if file_path == item.path:
                    return True
        except Exception:
            pass
    return False

if __name__ == "__main__":
    source_path = r"/volume1"
    dir_list = pathlib.Path(source_path).iterdir()
    #"@" appears in built-in directories in Synology that aren't shared folders.
    shared_folders = [d.__str__() for d in dir_list if d.is_dir() and not "@" in d.__str__()]
    file_path_tuple_lists = []
    for folder_path in shared_folders:
        file_path_tuples = []
        for root, subfolders, filenames in os.walk(folder_path):
            if "recycl" not in root and "Piyush_data_test" in root:
                for filename in filenames:
                    in_use = file_in_use(pathlib.Path(root).joinpath(
                        filename).__str__())
                    is_tif = filename.endswith("tif") or filename.endswith(
                        "tifffile")
                    if is_tif and not in_use:
                        file_path_tuples.append((root, filename))
        file_path_tuple_lists.append(file_path_tuples)
        png_dir_made = False
        for file_path_tuples in file_path_tuple_lists:
            if len(file_path_tuples) != 0:
                if not png_dir_made:
                    dest_path = pathlib.Path(folder_path).joinpath(
                        "png").__str__()
                    shutil.copytree(folder_path, 
                                    dest_path,
                                    ignore=shutil.ignore_patterns(
                                        '*.tifffile', 'tmp*', '*.tif'))
                    png_dir_made = True
                with Pool(psutil.cpu_count(logical=False)) as pool:
                    pool.map(png_conversion_task, file_path_tuples)