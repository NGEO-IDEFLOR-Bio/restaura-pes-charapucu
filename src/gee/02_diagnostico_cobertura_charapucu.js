/**
 * ==============================================================================
 * INVESTIGAÇÃO MULTIESCALA: MAPBIOMAS 10M, HISTÓRICO 1985-2025 E CANÓPIA S2
 * ==============================================================================
 */

var assetCharapucu = 'projects/ee-samuelsantosambientalcourse/assets/Parque_Estadual_Charapucu';
var pesCharapucu = ee.FeatureCollection(assetCharapucu);
var roi = pesCharapucu.geometry();

Map.centerObject(pesCharapucu, 11);
Map.setOptions('SATELLITE');

// 1. MapBiomas 10m Sentinel-2 (Coleção 4)
var asset10m = 'projects/mapbiomas-public/assets/brazil/lulc_10m/collection4/mapbiomas_10m_collection4_coverage_v1';
var mb10m = ee.Image(asset10m).clip(roi);
var bandas10m = mb10m.bandNames();
var ultimaBanda10m = bandas10m.get(bandas10m.size().subtract(1));
var mb10mRecente = mb10m.select(ee.String(ultimaBanda10m));

print('MapBiomas 10m (Sentinel-2) - Última banda:', ultimaBanda10m);

var hist10m = ee.Dictionary(mb10mRecente.reduceRegion({
  reducer: ee.Reducer.frequencyHistogram(),
  geometry: roi,
  scale: 10,
  maxPixels: 1e9
}).get(ee.String(ultimaBanda10m)));

print('📊 Classes no MapBiomas 10m (Código : Pixels 10x10m):', hist10m);

// 2. Histórico Completo MapBiomas 30m (1985 a 2025):
// Alguma vez algum pixel foi antrópico (15, 21, etc.) em qualquer ano da série?
var mb30m = ee.Image('projects/mapbiomas-public/assets/brazil/lulc/collection11/mapbiomas_brazil_collection11_coverage_v3').clip(roi);
var classesAntropicas = [15, 21, 24, 25, 30, 39, 41];

var historicoAntropico1985_2025 = ee.Image(
  mb30m.bandNames().iterate(function(nomeBanda, acc) {
    var b = mb30m.select(ee.String(nomeBanda));
    var ehAnt = b.remap(classesAntropicas, ee.List.repeat(1, classesAntropicas.length), 0);
    return ee.Image(acc).or(ehAnt);
  }, ee.Image(0))
);

var areaHistoricaAntropicaHa = historicoAntropico1985_2025.multiply(ee.Image.pixelArea()).divide(10000).reduceRegion({
  reducer: ee.Reducer.sum(),
  geometry: roi,
  scale: 30,
  maxPixels: 1e9
});

print('📜 Área Total Antrópica Histórica (1985-2025 acumulada em ha):', areaHistoricaAntropicaHa);

// 3. Dossel Aberto / Degradação no Sentinel-2 (10m)
// Filtrar imagem recente com menor nuvem
var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(roi)
  .filterDate('2024-07-01', '2024-11-30')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
  .median()
  .clip(roi);

var ndvi = s2.normalizedDifference(['B8', 'B4']).rename('NDVI');

// Máscara de água via MNDWI
var mndwi = s2.normalizedDifference(['B3', 'B11']).rename('MNDWI');
var terraFirmeEVárzea = mndwi.lt(0); // Apenas áreas secas/vegetadas

// Dossel com biomassa deprimida (NDVI < 0.65)
var dosselDeprimido = ndvi.lt(0.65).and(terraFirmeEVárzea);

var areaDosselDeprimidoHa = dosselDeprimido.multiply(ee.Image.pixelArea()).divide(10000).reduceRegion({
  reducer: ee.Reducer.sum(),
  geometry: roi,
  scale: 10,
  maxPixels: 1e9
});

print('🌿 Área com Dossel Ralo/Degradado (NDVI < 0.65 em 10m) (ha):', areaDosselDeprimidoHa.get('NDVI'));

// Camadas Visuais
Map.addLayer(pesCharapucu.style({color: 'cyan', width: 2, fillColor: '00000000'}), {}, 'PES Charapucu');
Map.addLayer(s2, {bands: ['B4', 'B3', 'B2'], min: 200, max: 2000}, 'Sentinel-2 RGB (2024)', false);
Map.addLayer(historicoAntropico1985_2025.selfMask(), {palette: ['orange']}, 'Antrópico Histórico (1985-2025)', true);
Map.addLayer(dosselDeprimido.selfMask(), {palette: ['red']}, 'Dossel Ralo / Degradado (NDVI < 0.65)', true);
