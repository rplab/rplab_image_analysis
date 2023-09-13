import json
import pathlib
from ast import literal_eval
from configparser import ConfigParser
from tifffile import TiffFile
from utils.files import FileSubtype, get_file_subtype

class MMMetadata(object):
    """
    Class to hold Micro-Manager metadata from Micro-Manager tif stack files.

    ## Constructor Parameters:

    file_path: str
        file path of MM tif image.
    """
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._metadata_dict: dict = self._get_metadata_dict()
        self.summary_metadata: dict = self._metadata_dict["Summary"]
        self.key_frames: list = [key for key in self._metadata_dict if "FrameKey" in key]
        self.dims: dict = self._get_dimensions()
        self.num_dims: int = len(self.dims)
        self.directory = str(pathlib.Path(file_path).parent)

    def _get_metadata_dict(self) -> dict:
        parent_file_generator = pathlib.Path(self.file_path).parent.iterdir()
        parent_files = [str(file) for file in parent_file_generator]
        for file in parent_files:
            if get_file_subtype(file) == FileSubtype.METADATA:
                return json.load(open(file))
        else:
            raise FileNotFoundError("MMMetadata file not found in directory.")
    
    def _get_dimensions(self) -> dict:
        stack = TiffFile(self.file_path)
        series = stack.series[0]
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

    def get_image_metadata(self, image_num: int):
        return MMImageMetadata(self, image_num)

class MMImageMetadata(object):
    def __init__(self, mm_metadata: MMMetadata, image_num: int):
        self._mm_metadata = mm_metadata
        self.image_num = image_num
        self.image_metadata: dict = mm_metadata._metadata_dict[mm_metadata.key_frames[image_num]]
        self.coords = self._get_coords()
        self.pixel_size = float(self.image_metadata["PixelSizeUm"])
        self.binning = int(self.image_metadata["Binning"])
        self.image_width = int(self.image_metadata["ROI"].split("-")[-2])
        self.image_height = int(self.image_metadata["ROI"].split("-")[-1]) 
        self.x_pos = float(self.image_metadata["XPositionUm"])
        self.y_pos = float(self.image_metadata["YPositionUm"])
        self.z_pos = float(self.image_metadata["ZPositionUm"])

    def get_coords_str(self):
        C = "channel"
        P = "position"
        T = "time"
        Z = "z"

        if "C" in self.coords.keys():
            channel_num = self.coords['C']
        else:
            channel_num = 0
        if "P" in self.coords.keys():
            position_num = self.coords['P']
        else:
            position_num = 0
        if "T" in self.coords.keys():
            time_num = self.coords['T']
        else:
            time_num = 0
        if "Z" in self.coords.keys():
            z_num = self.coords['Z']
        else:
            z_num = 0
        return f"{C}{channel_num:03d}_{P}{position_num:03d}_{T}{time_num:03d}_{Z}{z_num:03d}"
    
    def _get_coords(self):
        """
        returns dictionary with image coords. ie if the image is from z-slice 21 
        and taken with channel 2, coords_dict will be {"Z": 20, "C": 1}
        """
        dimensions = self._mm_metadata.dims
        quotient = self.image_num
        coords_dict = {}
        for item in dimensions.items():
            quotient, remainder = divmod(quotient, item[1])
            coords_dict[item[0]] = remainder
            if quotient == 0:
                break
        return coords_dict
    
class LSPycroMetadata(object):
    """
    Class to hold metadata from LSPycroApp. 

    ## Constructor Parameters:

    tif_file_path: str
        file path of MM tif image.
    """
    def __init__(self, tif_file_path: str):
        self._config = ConfigParser()
        self._init_config(tif_file_path)

    def _init_config(self, directory: str):
        file_generator = pathlib.Path(directory).iterdir()
        files = [str(file) for file in file_generator]
        for file in files:
            if get_file_subtype(file) == FileSubtype.LS_NOTES:
                self._config.read(file)
                break
        else:
            raise FileNotFoundError("LSPycroMetadata file not found in directory.")
    
    def get_section_dict(self, section: str) -> dict:
        section_dict = {}
        for item in self._config.items(section):
            section_dict[item[0]] = literal_eval(item[1])
        return section_dict
    
    def get_region_dict(self, fish_num: int, region_num: int) -> dict:
        section = f"Fish {fish_num} Region {region_num}"
        return self.get_section_dict(section)
    
def is_micro_manager(file_path: str | pathlib.Path):
    try:
        MMMetadata(file_path)
        return True
    except FileNotFoundError:
        return False