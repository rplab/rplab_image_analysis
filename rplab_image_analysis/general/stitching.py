import numpy as np
import skimage
import skimage.io
from general import downsample_image, get_max_projection
from utils.metadata import MMMetadata
from utils.files import FileSubtype, get_file_subtype


class Stitcher(object):
    """
    Class used to stitch images together. Currently only works with tif
    stack images taken in Micro-Manager.

    ### Constructor Parameters:

    file_list: list[str]
        list of image files to be stitched together
    
    save_path: str
        file path for image to be saved at. Should include filename and 
        extension. Supports any file extesion that is supported by
        skimage.io.imsave().

    ### Attributes:

    file_list: list[str]
        list of image files to be stitched together
    
    save_path: str
        file path for image to be saved at. Should include filename. Current
        supported file types to be saved as are tif and png.

    pixel_size: float = 0.1625
        pixel size in microns per pixel. Default value is for 6.5um camera 
        sensor pixel size and 40x objective.

    is_x_stage_inverted: bool = False
        Should be set True if the sample moving right is a negative x-stage
        position change. Else, should be set to False.

    is_y_stage_inverted: bool = False
        Should be set True if the sample moving up is a negative y-stage
        position change. Else, should be set to False.

    num_90_rotations: int = 0
        number of 90 degree rotations to be applied to images. Relevant
        because xy axes of camera may not line up with xy axes of stage, 
        so this aligns them. For Klamath, this should be zero, whereas for
        Willamette, it should be 3.

    downsample_factor: int = 1
        If images have been downsampled, this value should be equal to the
        factor the images were downsampled by. If images have not been 
        downsampled from their original, changing this value will cause
        images to be downsampled by downsample_factor before being stitched.
    
    """
    def __init__(self, file_list: list[str], save_path: str):
        self.file_list = file_list
        self.save_path = save_path
        self.pixel_size = 0.1625
        self.x_stage_is_inverted = False
        self.y_stage_is_inverted = False
        self.num_90_rotations = 0
        self.downsample_factor = 1

    def stitch_images(self):
        # x_range and y_range contain current min and max pixel positions.
        # ie, if the first image added is a 2048x2048 pixel image, both
        # x_range and y_range become [0,2048].
        file_subtype = get_file_subtype(self.file_list[0])
        if file_subtype == FileSubtype.MMSTACK:
            stitched_image = self._stitch_mm_images()
        skimage.io.imsave(self.save_path, stitched_image, check_contrast=False)

    def _stitch_mm_images(self):
        stitched_x_range = [0, 0]
        stitched_y_range = [0, 0]
        stitched_image = np.zeros(0)
        for region_num, file_path in enumerate(self.file_list):
            first_metadata = MMMetadata(file_path).get_image_metadata(0)
            image_width = int(first_metadata["ROI"].split("-")[2])
            image_height = int(first_metadata["ROI"].split("-")[3]) 
            x_pos = first_metadata["XPositionUm"]
            y_pos = first_metadata["YPositionUm"]

            new_image = get_max_projection(file_path)
            #Assumption is that same downscale factor is used for both
            #dimensions of image
            if new_image.shape[0] != image_height:
                self.downscale_factor = int(image_width/new_image.shape[0])
            elif self.downsample_factor != 1:
                new_image = downsample_image(new_image, self.downscale_factor)

            new_image = np.rot90(new_image, k=self.num_90_rotations)
            if self.num_90_rotations % 2 == 1:
                image_width, image_height = image_height, image_width
            image_dims = [image_width, image_height]

            if region_num == 0:
                stitched_image = new_image
                start_x_pos = x_pos
                start_y_pos = y_pos
                stitched_x_range[1] = image_dims[0]
                stitched_y_range[1] = image_dims[1]
                pixel_size = first_metadata["PixelSizeUm"]
                binning = first_metadata["Binning"]
                self.pixel_size = pixel_size*binning*self.downsample_factor
            else:
                x_stage_offset = self._get_pixel_offset(start_x_pos, x_pos)
                x_stage_offset *= -1 if self.x_stage_is_inverted else 1
                y_stage_offset = self._get_pixel_offset(start_y_pos, y_pos)
                y_stage_offset *= -1 if self.y_stage_is_inverted else 1
                stitched_image = self._stitch_new_image(new_image, 
                                                        stitched_image, 
                                                        x_stage_offset, 
                                                        y_stage_offset, 
                                                        image_dims, 
                                                        stitched_x_range, 
                                                        stitched_y_range)
        return stitched_image
            
    def _get_pixel_offset(self, start_um, end_um) -> int:
        """
        Calculates pixel offset between images based on difference in 
        stage positions and returns it.
        """
        return round((end_um - start_um)/self.pixel_size)
    
    def _stitch_new_image(self, 
                          new_image: np.ndarray, 
                          stitched_image: np.ndarray, 
                          x_stage_offset: int, 
                          y_stage_offset: int, 
                          image_dims: list[int, int], 
                          stitched_x_range: list[int, int], 
                          stitched_y_range: list[int, int]
        ) -> np.ndarray:
        """
        Stitches new_image with stitched_image based on stage positions in
        Micro-Manager metadata.
        """
        new_image_x_range, new_image_y_range = self._get_new_image_range(
            x_stage_offset, y_stage_offset, image_dims)
        x_extensions, y_extensions = self._get_stitched_extensions(
            stitched_x_range, stitched_y_range, new_image_x_range, 
            new_image_y_range)
        stitched_x_range[0] = min(stitched_x_range[0], new_image_x_range[0])
        stitched_y_range[0] = min(stitched_y_range[0], new_image_y_range[0])
        stitched_x_range[1] = max(stitched_x_range[1], new_image_x_range[1])
        stitched_y_range[1] = max(stitched_y_range[1], new_image_y_range[1])
        
        stitched_image = self._add_stitched_extensions(
            stitched_image, x_extensions, y_extensions)
        slices = self._get_new_image_position_slices(
            x_extensions, y_extensions, image_dims)
        #If two images are added with the same stage position (ie, if z-stack 
        # is split into two files because it's too large for one), second region
        #would just overwrite the first. This takes a max projection of the
        #newly added region and the previously added one so this doesn't 
        #happen.
        stitched_region = stitched_image[slices[1], slices[0]]
        region_array = np.array((stitched_region, new_image))
        new_region = np.max(region_array, 0)
        stitched_image[slices[1], slices[0]] = new_region
        return stitched_image
    
    def _get_new_image_range(self, 
                             x_stage_offset: int, 
                             y_stage_offset: int, 
                             image_dims: list[int, int]
        ) -> tuple[list[int], list[int]]:
        """
        Gets min and max pixel positions of new_image based on x_stage_offset,
        y_stage_offset, and width and height of new_image.
        """
        x_range = [x_stage_offset, x_stage_offset + image_dims[0]]
        y_range = [y_stage_offset, y_stage_offset + image_dims[1]]
        return (x_range, y_range)

    def _get_stitched_extensions(self, 
                                 stitched_x_range: list[int], 
                                 stitched_y_range: list[int], 
                                 new_image_x_range: list[int], 
                                 new_image_y_range: list[int]
        ) -> tuple[list[int, int], list[int, int]]:
        """
        Gets stitched extensions--number of rows and columns to be concatenated
        to stitched_image--to make room for new_image to be added.
        """
        x_min_extension = stitched_x_range[0] - new_image_x_range[0]
        x_max_extension = new_image_x_range[1] - stitched_x_range[1]
        y_min_extension = stitched_y_range[0] - new_image_y_range[0]
        y_max_extension = new_image_y_range[1] - stitched_y_range[1]
        x_extensions = [x_min_extension, x_max_extension]
        y_extensions = [y_min_extension, y_max_extension]
        return (x_extensions, y_extensions)

    def _add_stitched_extensions(self, 
                                 stitched_image: np.ndarray, 
                                 x_extensions: list[int, int], 
                                 y_extensions: list[int, int]
        ) -> np.ndarray:
        """
        Concatenates image extensions and stitched image. Image extensions
        are arrays of zeros that are added to the left, right, top, and bottom
        of stitched_image to make space for newly added new_image.
        """
        dtype = stitched_image.dtype
        if x_extensions[0] > 0:
            extension = np.zeros([stitched_image.shape[0], x_extensions[0]])
            stitched_image = np.c_[extension, stitched_image]

        if x_extensions[1] > 0:
            extension = np.zeros([stitched_image.shape[0], x_extensions[1]])
            stitched_image = np.c_[stitched_image, extension]

        if y_extensions[0] > 0:
            extension = np.zeros([y_extensions[0], stitched_image.shape[1]])
            stitched_image = np.concatenate([extension, stitched_image])

        if y_extensions[1] > 0:
            extension = np.zeros([y_extensions[1], stitched_image.shape[1]])
            stitched_image = np.concatenate([stitched_image, extension])

        #numpy concatenation doesn't seem to conserve datatype, so ensure
        #datatype is same as original stitched image.
        return stitched_image.astype(dtype)

    def _get_new_image_position_slices(self, 
                                       x_extensions: list[int, int], 
                                       y_extensions: list[int, int], 
                                       image_dims: list[int, int]
        ) -> tuple[slice, slice]:
        """
        Gets image position slices where new_image will be inserted
        into stitched_image array.
        """
        if x_extensions[0] > 0:
            x_slice = slice(0, image_dims[0])
        else:
            x_slice = slice(-x_extensions[0], image_dims[0] - x_extensions[0])

        if y_extensions[0] > 0:
            y_slice = slice(0, image_dims[1])
        else:
            y_slice = slice(-y_extensions[0], image_dims[1] - y_extensions[0])

        return (x_slice, y_slice)
