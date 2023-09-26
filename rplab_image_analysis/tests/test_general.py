import numpy as np
from rplab_image_analysis.general.max_projections import create_batch_max_projections
from rplab_image_analysis.general.downsampling import get_downsampled_image, downsample_batch
from rplab_image_analysis.general.downsampling import _get_downsample_tuple
from rplab_image_analysis.general.stitching import stitch_images
from rplab_image_analysis.general.png_conversion import batch_convert_to_pngs
from rplab_image_analysis.general.background_subtraction import median_subtract_batch


class TestDownsample(object):
    def test_get_downsample_tuple(self):
        test_image = np.ones([5, 40, 400, 800])
        downsample_tuple = _get_downsample_tuple(len(test_image.shape), 4)
        assert downsample_tuple == (1, 1, 4, 4)

    def test_get_downsampled_image(self):
        test_image = np.ones([200, 400, 400])
        downsampled_image = get_downsampled_image(test_image, 4)
        assert downsampled_image.shape == (200, 100, 100)

    def test_downsample_batch(self):
        source_dir = r"Z:\21June2023 Overnight\Acquisition\fish1\pos1\zstack\GFP"
        dest_dir = r"Z:\JGTEST\downsample_test"
        downsample_batch(source_dir, dest_dir, 4)


class TestMaxProjections(object):
    def test_create_batch_max_projections(self):
        source_dir = r"Z:\21June2023 Overnight\Acquisition\fish1\pos1\zstack\GFP\timepoint1"
        dest_dir = r"Z:\JGTEST\max_projection_test"
        create_batch_max_projections(source_dir, dest_dir)


class TestStitching(object):
    def test_stitch_images(self):
        base_dir = r"Z:\25Sept2023 Fixed Fish\GF\Fish 2\Acquisition\fish1\pos1\zstack\gfp\timepoint1\fish1_pos1_zstack_GFP_timepoint1_MMStack.ome.tif"
        pos_nums = [1,2,3,4]
        paths = [base_dir.replace("pos1", f"pos{pos_num}") for pos_num in pos_nums]

        save_path = r"C:\Jonah\Misc\Julia\GF Fish 2\stitched_gfp.tif"
        stitch_images(paths, save_path, num_90_rotations=3,
                      x_stage_is_inverted=True)


class TestPngConversion(object):
    def test_batch_convert_to_pngs(self):
        source_dir = r"Z:\21June2023 Overnight\Acquisition\fish1\pos1\zstack\GFP"
        dest_dir = r"Z:\JGTEST\png_conversion_test"
        batch_convert_to_pngs(source_dir, dest_dir)


class TestBackgroundSubtraction(object):
    def test_background_subtract_batch(self):
        source_dir = r"Z:\21June2023 Overnight\Acquisition\fish1\pos1\zstack\GFP\timepoint1"
        dest_dir = r"Z:\JGTEST\background_subtract_test"
        median_subtract_batch(source_dir, dest_dir)
