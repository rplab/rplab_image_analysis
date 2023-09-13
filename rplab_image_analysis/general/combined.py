def combined_batch_process(source_dir: str, 
                           dest_dir: str, 
                           downsample_factor: int = 1,
                           subtract_background: bool = False,
                           max_projection: bool = False,
                           convert_to_png: bool = False):
    