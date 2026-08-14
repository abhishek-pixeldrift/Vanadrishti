import json
from shapely.geometry import shape
import pyproj
from shapely.ops import transform

geojson = {'type': 'Polygon', 'crs': {'type': 'name', 'properties': {'name': 'EPSG:4326'}}, 'coordinates': [[[73.79520049687986, 20.0063], [73.79667489037243, 20.00937868518357], [73.79318331785116, 20.00985341577279], [73.791, 20.01012254314951], [73.78748660300387, 20.012018159770204], [73.78757622658067, 20.00815743156365], [73.7842458318916, 20.0063], [73.78484345785054, 20.00296001387628], [73.78728490588327, 20.00025357207164], [73.791, 19.999827026038318], [73.79468864590167, 20.000296617340787], [73.79605265745813, 20.00355888243946], [73.79520049687986, 20.0063]]]}

geom = shape(geojson)

# Create a transformer from EPSG:4326 (lat/lon) to EPSG:3857 (meters) to get approximate area
# For more accuracy, use an equal-area projection or geodesic
project = pyproj.Transformer.from_crs('EPSG:4326', 'EPSG:3857', always_xy=True).transform
geom_m = transform(project, geom)

area_sqm = geom_m.area
# EPSG 3857 distorts area, so we better use geodesic (pyproj Geod)
geod = pyproj.Geod(ellps="WGS84")
area_sqm, perim = geod.geometry_area_perimeter(geom)
area_ha = abs(area_sqm) / 10000.0

print(f"Area: {abs(area_sqm)} sqm")
print(f"Area: {area_ha} ha")
print(f"Displayed area in DB: 12.5 ha")
