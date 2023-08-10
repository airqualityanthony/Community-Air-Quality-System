
from osdatahub import FeaturesAPI, Extent

key = "tiZBA5AnyMgDvPt5nbADwzhs8oGpy0pJ"
bbox = (-2.2361, 53.4746, -2.2234, 53.4805)
extent = Extent.from_bbox(bbox, "EPSG:4326")

product = "Zoomstack_DistrictBuildings"
features = FeaturesAPI(key, product, extent)
results = features.query()

print(results)