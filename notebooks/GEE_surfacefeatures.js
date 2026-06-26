
var REGION_NAME = 'Garhwal-Himalaya';
var WEST = 78.2;
var SOUTH = 30.0;
var EAST= 80.0;
var NORTH = 31.0;
var START_DATE = '2023-01-01';
var END_DATE= '2023-12-31';
var NUM_POINTS = 5000;



// Define study area from parameters above
var studyArea = ee.Geometry.Rectangle([WEST, SOUTH, EAST, NORTH]);

Map.centerObject(studyArea, 10);
Map.addLayer(studyArea, {color: 'blue'}, 'Study Area: ' + REGION_NAME);

// Load SRTM DEM and compute terrain features
var dem = ee.Image('USGS/SRTMGL1_003').clip(studyArea);

var slope = ee.Terrain.slope(dem);
var aspect = ee.Terrain.aspect(dem);
var curvature = dem.convolve(ee.Kernel.laplacian8());

Map.addLayer(slope, {min:0, max:60, palette:['green','yellow','red']}, 'Slope');

// load landsat 8 and calculate ndvi
var landsat = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
  .filterBounds(studyArea)
  .filterDate('2018-01-01', '2023-12-31')
  .filter(ee.Filter.lt('CLOUD_COVER', 30))
  .map(function(img) {

    // Apply official Landsat scaling factors
    var opticalBands = img.select('SR_B.').multiply(0.0000275).add(-0.2);

    // Cloud mask using QA_PIXEL band
    var qa = img.select('QA_PIXEL');
    var cloudMask = qa.bitwiseAnd(1 << 3).eq(0)  // cloud shadow
      .and(qa.bitwiseAnd(1 << 4).eq(0))           // snow
      .and(qa.bitwiseAnd(1 << 5).eq(0));           // cloud

    return img.addBands(opticalBands, null, true)
              .updateMask(cloudMask);
  })
  .median()
  .clip(studyArea);

// Landsat 8 bands: SR_B5 = NIR, SR_B4 = Red
var ndvi30 = landsat.normalizedDifference(['SR_B5', 'SR_B4'])
  .rename('NDVI');

// Visualize
Map.addLayer(ndvi30, {min:0.0, max:0.8,
  palette:['red','yellow','green']}, 'NDVI Landsat8');

// Check image count
var count = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
  .filterBounds(studyArea)
  .filterDate('2018-01-01', '2023-12-31')
  .filter(ee.Filter.lt('CLOUD_COVER', 30))
  .size();
print('Landsat images found:', count);

// Sample specific points to verify variation
var testPoints = ee.FeatureCollection([
  ee.Feature(ee.Geometry.Point([79.5, 30.4]), {name: 'high_altitude'}),
  ee.Feature(ee.Geometry.Point([78.5, 30.1]), {name: 'low_valley'}),
  ee.Feature(ee.Geometry.Point([79.0, 30.6]), {name: 'mid_slope'}),
  ee.Feature(ee.Geometry.Point([78.8, 30.3]), {name: 'forest_zone'})
]);

var sampled = ndvi30.sampleRegions({
  collection: testPoints,
  scale: 30,
  properties: ['name']
});

print('NDVI at test points:', sampled);
var ndviStats = ndvi30.reduceRegion({
  reducer : ee.Reducer.minMax(),
  geometry : studyArea,
  scale : 500,
  maxPixels: 1e9
});
print('NDVI min and max:', ndviStats);

// Load CHIRPS rainfall
var rainfall = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
  .filterDate('2020-01-01', END_DATE)
  .mean()
  .multiply(365)
  .clip(studyArea)
  .rename('rainfall');

Map.addLayer(rainfall, {min:500, max:3000, palette:['white','blue']}, 'Rainfall');

// STEP 5: Stack all features
var featureStack = dem.rename('elevation')
  .addBands(slope.rename('slope'))
  .addBands(aspect.rename('aspect'))
  .addBands(curvature.rename('curvature'))
  .addBands(ndvi30.rename('NDVI'))
  .addBands(rainfall.rename('rainfall'));

print('Feature bands:', featureStack.bandNames());

// Sample points
var samples = featureStack.sample({
  region: studyArea,
  scale : 30,
  numPixels : NUM_POINTS,
  seed: 42,
  geometries: true
});

print('Number of sample points:', samples.size());
print('First point example:', samples.first());

// Export 
Export.table.toDrive({
  collection: samples,
  description : 'surface features' + REGION_NAME,
  fileFormat: 'CSV',
  folder : 'byop_surface_features'
});