from utils.metadata import MMMetadata

class TestMMMetadata(object):
    def test_get_image_metadata(self):
        file_path = r"C:\Jonah\Misc\Bead Images\Original Stack\beads_MMStack_Pos0.ome.tif"
        metadata = MMMetadata(file_path)
        image_metadata = metadata.get_image_metadata(10)
        assert image_metadata["ZPositionUm"] == 480.23
    
    def test_image_dims(self):
        file_path = r"C:\Jonah\Misc\Bead Images\Original Stack\beads_MMStack_Pos0.ome.tif"
        dims = MMMetadata(file_path).dims
        shape = []
        for key in dims.keys():
            shape.append(dims[key])
        shape = tuple(shape)
        print(shape)
