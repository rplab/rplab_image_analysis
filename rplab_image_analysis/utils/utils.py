def is_ls_pycro_metadata(file_path: str):
    return "notes" in file_path and file_path.endswith("txt")  

def is_mm_metadata(file_path: str):
    return "metadata" in file_path and file_path.endswith("txt")

def is_tif(file_path: str):
    file_path.endswith("tif") or file_path.endswith("tiff")

def is_tif(file_path: str):
    file_path.endswith("png")
