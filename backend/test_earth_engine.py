import ee

PROJECT_ID = "ecotrack-ndvi"

ee.Initialize(project=PROJECT_ID)

print(ee.String("Earth Engine connected successfully").getInfo())