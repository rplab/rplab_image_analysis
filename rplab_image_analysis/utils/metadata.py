import json
import pathlib
from ast import literal_eval
from configparser import ConfigParser
from utils.files import FileSubtype, get_file_subtype

class MMMetadata(object):
    def __init__(self, directory: str):
        self._metadata_dict: dict = self._get_metadata_dict(directory)
        self.summary_metadata: dict = self._metadata_dict["Summary"]
        self.key_frames: list = [key for key in self._metadata_dict if "FrameKey" in key]

    def _get_metadata_dict(self, directory: str) -> dict:
        if get_file_subtype(directory) == FileSubtype.METADATA:
            return json.load(open(directory))
        else:
            parent_file_generator = pathlib.Path(directory).parent.iterdir()
            parent_files = [str(file) for file in parent_file_generator]
            for file in parent_files:
                if get_file_subtype(file) == FileSubtype.METADATA:
                    return json.load(open(file))
  
    def get_image_metadata(self, image_num: int) -> dict:
        return self._metadata_dict[self.key_frames[image_num]]


class LSPycroMetadata(object):
    def __init__(self, directory: str):
        self._config = ConfigParser()
        self._init_config(directory)

    def _init_config(self, directory: str):
        if get_file_subtype(directory) == FileSubtype.LS_NOTES:
            self._config.read(directory)
        else:
            file_generator = pathlib.Path(directory).iterdir()
            files = [str(file) for file in file_generator]
            for file in files:
                if get_file_subtype(file) == FileSubtype.LS_NOTES:
                    self._config.read(file)
                    break
    
    def get_section_dict(self, section: str) -> dict:
        section_dict = {}
        for item in self._config.items(section):
            section_dict[item[0]] = literal_eval(item[1])
        return section_dict
    
    def get_region_dict(self, fish_num: int, region_num: int) -> dict:
        section = f"Fish {fish_num} Region {region_num}"
        return self.get_section_dict(section)

