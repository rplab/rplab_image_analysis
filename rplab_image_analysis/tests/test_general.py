import numpy as np
from general.downsampling import downsample_image
from general.downsampling import _get_downsample_tuple
from general.stitching import Stitcher

class TestDownsample(object):
    def test_get_downsample_tuple(self):
        test_image = np.ones([200, 400, 400])
        downsample_tuple = _get_downsample_tuple(len(test_image.shape), 4)
        assert downsample_tuple == (1, 4, 4)

    def test_downsample_image(self):
        test_image = np.ones([200, 400, 400])
        downsampled_image = downsample_image(test_image, 4)
        assert downsampled_image.shape == (200, 100, 100)

class TestStitching(object):
    def test_stitching(self):
        base_dir = r"Z:\7Jun2023 Overnight\Acquisition\fish1\pos1\zstack\GFP\timepoint1\fish1_pos1_zstack_GFP_timepoint1_MMStack.ome.tif"
        pos_nums = [1,2,3,4]
        paths = [base_dir.replace("pos1", f"pos{pos_num}") for pos_num in pos_nums]

        save_path = r"C:\Jonah\Misc\stitcher_test\stitched.tif"
        stitcher = Stitcher(paths, save_path)
        stitcher.num_90_rotations = 3
        stitcher.x_stage_is_inverted = True
        stitcher.stitch_images()
