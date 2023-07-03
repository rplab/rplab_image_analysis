from utils.metadata import LSPycroMetadata

directory = r"Z:\7Jun2023 Overnight\Acquisition"
thing = LSPycroMetadata(directory)
fish = thing.get_region_dict(1,1)