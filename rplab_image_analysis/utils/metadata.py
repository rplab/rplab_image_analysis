import json
import pathlib
from ast import literal_eval
from configparser import ConfigParser

from rplab_image_analysis.utils import files, file_types


#metadata classes and functions
class MMMetadata(object):
    """
    Class to hold Micro-Manager metadata from Micro-Manager tif stack files.

    ## Constructor Parameters:

    file_path: str
        file path of MM tif image.

    Raises FileNotFoundError if metadata isn't found.
    """
    #Possible axes in Micro-Manager metadata
    _Z = "z"
    _CHANNEL = "channel"
    _TIME = "time"
    _POSITION = "position"

    def __init__(self, file_path: str | pathlib.Path):
        self.file_path: str | pathlib.Path = file_path
        self.metadata: dict = self._init_metadata()
        self.summary_metadata: dict = self.metadata["Summary"]
        self.axis_order: list[str] = self._get_axis_order()
        self.frame_keys: list = [k for k in self.metadata if "FrameKey" in k]
        self.image_width: int = int(self.summary_metadata["Width"])
        self.image_height: int = int(self.summary_metadata["Height"])
        self.dims: dict = self._get_dimensions()
        self.num_dims: int = len(self.dims)
        self.num_channels: int = int(self.summary_metadata["Channels"])
        self.num_tps: int = int(self.summary_metadata["Frames"])
        self.directory = str(pathlib.Path(file_path).parent)
        self.all_filenames: list = self._get_all_filenames()
        self.is_multifile: bool = len(self.all_filenames) > 1

    def get_filename_start_num(self, filename: str | pathlib.Path):
        """
        Returns frame key number where filename is first used in metadata.
        """
        filename = pathlib.Path(filename).name
        for key in self.frame_keys:
            meta_filename = self.metadata[key]["FileName"]
            if filename == meta_filename:
                return self.frame_keys.index(key)

    def get_image_metadata(self, image_num: int):
        """
        Returns image metadata as MMImageMetadata object.
        """
        return MMImageMetadata(self, image_num)

    def get_framekey_coords(self, framekey_num: int) -> dict:
        """
        Returns coords of given framekey_num.
        """
        framekey_coords = {}
        #Order of framekeys is Framekey-(time)-(channel)-(z)
        framekey_nums = self.frame_keys[framekey_num].split("-")[1:]
        framekey_coords[MMMetadata._Z] = int(framekey_nums[2])
        framekey_coords[MMMetadata._CHANNEL] = int(framekey_nums[1])
        framekey_coords[MMMetadata._TIME] = int(framekey_nums[0])
        return framekey_coords

    def _init_metadata(self) -> dict:
        """
        Initializes metadata from metadata file.

        Raises FileNotFoundError if metadata isn't found.
        """
        file_path = pathlib.Path(self.file_path)
        if file_path.is_file():
            if file_types.is_mm_metadata(file_path):
                return json.load(open(file_path))
            elif file_types.is_image(file_path):
                dir = file_path.parent
        elif file_path.is_dir():
            dir = file_path
        file_generator = dir.iterdir()
        dir_files = [file for file in file_generator]
        image_file_name = pathlib.Path(self.file_path).name
        #splits filename at .ome to see if metadata file in folder contains
        #file name as substring. Text after .ome is not included in metadata
        #file name.
        image_file_name = image_file_name.split(
            file_types.FileSubtype.OME.value)[0]
        for file in dir_files:
            name_matches = image_file_name in file.name
            if file_types.is_mm_metadata(file_path) and name_matches:
                return json.load(open(file))
        else:
            #If no metadata file is found that matches name of image, assume
            #only there's only one metadata file is in folder that doesn't 
            #match name.
            for file in dir_files:
                if file_types.is_mm_metadata(file):
                    return json.load(open(file))  
        raise FileNotFoundError("MMMetadata file not found in directory.")

    def _get_axis_order(self) -> list[str]:
        """
        Returns axis order found in summary metadata.
        """
        axis_order: list = self.summary_metadata["AxisOrder"]
        #Delete position axis because images at different x-y stage positions
        #in MM are saved in different files with different metadata files.
        axis_order.remove(self._POSITION)
        return axis_order

    def _get_dimensions(self) -> dict:
        """
        Returns intended dimensions found in summary metadata.
        """
        intended_dims = self.summary_metadata["IntendedDimensions"]
        dims = {}
        for axis in self.axis_order:
            dims[axis] = int(intended_dims[axis])
        return dims

    def _get_all_filenames(self):
        """
        Returns list of all filenames found in metadata file.
        """
        filenames = []
        for key in self.frame_keys:
            filename = self.metadata[key]["FileName"]
            if filename not in filenames:
                filenames.append(filename)
        return filenames
    

class MMImageMetadata(object):
    def __init__(self, mm_metadata: MMMetadata, image_index: int):
        self._mm_metadata: MMMetadata = mm_metadata
        self.image_index: int = image_index
        self.framekey: str = mm_metadata.frame_keys[image_index]
        self.image_metadata: dict = mm_metadata.metadata[self.framekey]
        self.coords: dict = self._get_coords()
        self.pixel_size: float = float(self.image_metadata["PixelSizeUm"])
        self.binning: int = int(self.image_metadata["Binning"])
        self.image_width: int = int(self.image_metadata["ROI"].split("-")[-2])
        self.image_height: int = int(self.image_metadata["ROI"].split("-")[-1]) 
        self.x_pos: float = float(self.image_metadata["XPositionUm"])
        self.y_pos: float = float(self.image_metadata["YPositionUm"])
        self.z_pos: float = float(self.image_metadata["ZPositionUm"])

    def get_coords_str(self):
        """
        Returns coords as string. 
        """
        coords_str = ""
        for item in self.coords.items():
            coords_str = f"{coords_str}_{item[0]}{item[1]:03d}"
        return coords_str.strip("_")
    
    def _get_coords(self):
        """
        returns dictionary with image coords. ie if the image is from 
        z-slice 21 and taken with channel 2, coords_dict will be 
        {"Z": 20, "C": 1}
        """
        #Since this is meant to represent the same coord information that's 
        #found in each framekey, I originally thought I could just use the 
        #framekey to determine coordinates of each image. However, which 
        #coordinate position in each framekey corresponds to which coordinate 
        #label (C, Z, T, etc.), which one would think would be determined by
        #the "Axis Order" property, isn't consistent (sometimes reverse order,
        #other times not). Instead, coords are determined by an algorithm
        #that matches image index with permutation of dimensions, which
        #correctly aligns with framekey.
        dimensions = self._mm_metadata.dims
        framekey_coords = self._mm_metadata.get_framekey_coords(self.image_index)
        coords = {}
        for key in dimensions.keys():
            if dimensions[key] != 1:
                coords[key] = framekey_coords[key]
        return coords


class LSPycroMetadata(ConfigParser):
    """
    Class to hold metadata from LSPycroApp. 
    
    This metadata is written and stored via ConfigParser class, so this class
    implements ConfigParser and contains some additional methods for accessing
    sections specific to the LSPycroMetadata.

    ## Constructor Parameters:

    path: str
        Can be path of tif file, directory of tif file, ls notes file,
        or directory of notes file. If LS Pycro metadata file is not found
        in directory, will recursively search for it.

    Raises FileNotFoundError if metadata isn't found.
    """
    #Name of acquisition folder. 
    ACQUISITION = "Acquisition"
    FISH = "Fish"
    REGION = "Region"

    def __init__(self, path: str | pathlib.Path):
        self._init_config(path)

    def _init_config(self, path: str | pathlib.Path):
        """
        Inits ConfigParser config from metadata file.

        Raises FileNotFoundError if metadata isn't found.
        """
        path = pathlib.Path(path)
        if path.is_file() and file_types.is_ls_pycro_notes(path):
            self.read(file)
        elif self.ACQUISITION in path:
            cur_directory = path
            while self.ACQUISITION not in cur_directory.name:
                cur_directory = cur_directory.parent
            file_generator = pathlib.Path(cur_directory)
            file_list = [str(file) for file in file_generator]
            for file in file_list:
                if file_types.is_ls_pycro_notes(file):
                    self.read(file)
                    break
            else:
                raise FileNotFoundError("LSPycroMetadata file not found.")
        else:
            raise FileNotFoundError("LSPycroMetadata file not found.")
    
    def get_section_dict(self, section: str) -> dict:
        """
        Returns dict of section in config file.
        """
        section_dict = {}
        for item in self.items(section):
            section_dict[item[0]] = literal_eval(item[1])
        return section_dict
    
    def get_region_dict(self, fish_num: int, region_num: int) -> dict:
        """
        Returns dict of region in config file.
        """
        section = self._get_region_section(fish_num, region_num)
        return self.get_section_dict(section)
    
    def get_num_fish(self) -> int:
        """
        Returns number of fish in config file.
        """
        num_fish = 0
        for section in self.sections():
            if self.FISH in section and self.REGION in section:
                num_fish += 1
        return num_fish
    
    def get_num_regions(self, fish_num: int) -> int:
        """
        Returns number of regions in config file.
        """
        #Start at 1 because region names start with "Region 1"
        region_num = 1
        section = self._get_region_section(fish_num, region_num)
        while self.has_section(section):
            region_num += 1
            section = self._get_region_section(fish_num, region_num)
        return region_num - 1

    def _get_region_section(self, fish_num: int, region_num: int) -> str:
        """
        Returns config section with given fish_num and region_num.
        """
        return f"{self.FISH} {fish_num} {self.REGION} {region_num}"
    

def from_same_mm_sequence(file_list: list[str | pathlib.Path]) -> bool:
    first_file = pathlib.Path(file_list[0])
    if is_mm(first_file):
        first_name = files.get_reduced_filename(pathlib.Path(file_list[0]))
        for file in file_list[1:]:
            filename = files.get_reduced_filename(pathlib.Path(file))
            is_same_series = filename in first_name or first_name in filename
            if not is_same_series:
                return False
        else:
            return True
    else:
        return False
    

def is_mm(file_path: str | pathlib.Path) -> bool:
    """
    If file_path is an MM metadata file or file_path directory contains 
    MM metadata file, returns True
    """
    try:
        MMMetadata(file_path)
        return True
    except FileNotFoundError:
        return False
    