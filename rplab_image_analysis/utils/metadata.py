import json
import pathlib
from ast import literal_eval
from configparser import ConfigParser
from utils.utils import is_mm_metadata, is_ls_pycro_metadata

class MMMetadata(object):
    def __init__(self, directory: str):
        self._init_metadata_dict(directory)
        self.summary_metadata: dict = self._metadata_dict["Summary"]
        self.image_key_frames: list = [key for key in self._metadata_dict if "FrameKey" in key]

    def _init_metadata_dict(self, directory):
        if is_mm_metadata(directory):
            self._metadata_dict: dict = json.load(open(directory))
        else:
            file_list = [str(file) for file in pathlib.Path(directory).iterdir()]
            for file in file_list:
                if is_mm_metadata(file):
                    self._metadata_dict: dict = json.load(open(file))
                    break
    
    def get_image_metadata(self, image_num):
        return self._metadata_dict[self.image_key_frames[image_num]]


class LSPycroMetadata(object):
    def __init__(self, directory: str):
        super().__init__()
        self._init_config(directory)
        self._config = ConfigParser()

    def _init_config(self, directory):
        if is_ls_pycro_metadata(directory):
            self._config.read(directory)
        else:
            file_list = [str(file) for file in pathlib.Path(directory).iterdir()]
            for file in file_list:
                if is_ls_pycro_metadata(file):
                    self._config.read(file)
                    break
    
    def get_section_dict(self, section):
        section_dict = {}
        for item in self._config.items(section):
            section_dict[item[0]] = literal_eval(item[1])
        return section_dict
    
    def get_region_dict(self, fish_num, region_num):
        section = f"Fish {fish_num} Region {region_num}"
        return self.get_section_dict(section)

