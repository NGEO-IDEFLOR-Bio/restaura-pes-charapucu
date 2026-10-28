/**
 * ==============================================================================
 * PROJETO: Banco de Áreas Elegíveis para Restauração Florestal — PES Charapucu
 * ÓRGÃO: Núcleo de Geotecnologias (NGEO) / IDEFLOR-Bio
 * AMBIENTE: Google Earth Engine (GEE Code Editor)
 * ==============================================================================
 * VERSÃO BLINDADA CONTRA CORPOS D'ÁGUA, FUROS E CANAIS DE MARÉ:
 * 1. Limite Oficial do PES Charapucu.
 * 2. MÁSCARA HÍDRICA MULTIFONTE RIGOROSA:
 *    - JRC Global Surface Water (occurrence > 5% ou max_extent)
 *    - MapBiomas Coleção 11 (Classe 33 - Água) acumulada
 *    - Sentinel-2 MNDWI (Green - SWIR) para detectar água barrenta / turbilhonada
 *    - Piso mínimo de reflectância SWIR (elimina água sedimentada)
 *    - Buffer de exclusão da orla de maré (40 metros)
 * 3. Piso Mínimo de Biomassa Vegetal (NDVI >= 0.40):
 *    - Elimina sedimentos fluviais expostos na maré baixa
 * 4. Detecção de Áreas Terrestres Elegíveis (Mosaico/Campos e Várzea Raleada).
 * 5. Estratificação Metodológica (RNA, Enriquecimento, Plantio Direto).
 * 6. Vetorização e Exportação.
 * ==============================================================================
 */

// ------------------------------------------------------------------------------
// 1. LIMITE DO PARQUE
// ------------------------------------------------------------------------------
var assetCharapucu = 'projects/ee-samuelsantosambientalcourse/assets/Parque_Estadual_Charapucu';
var pesCharapucu = ee.FeatureCollection(assetCharapucu);
var roi = pesCharapucu.geometry();

Map.centerObject(pesCharapucu, 11);
Map.setOptions('SATELLITE');
Map.addLayer(pesCharapucu.style({color: 'cyan', width: 2, fillColor: '00000000'}), {}, 'Limite Oficial - PES Charapucu');

// ------------------------------------------------------------------------------
// 2. MÁSCARA HÍDRICA MULTIFONTE (ELIMINAÇÃO TOTAL DE RIOS E FUROS)
// ------------------------------------------------------------------------------
// A) JRC Global Surface Water (Histórico de 38 anos)
var jrc = ee.Image('JRC/GSW1_4/GlobalSurfaceWater').clip(roi);
var jrcAgua = jrc.select('occurrence').gt(5).or(jrc.select('max_extent').eq(1));

// B) MapBiomas Coleção 11 - Classe 33 (Corpos d'Água) nos últimos anos
var assetMapBiomas = 'projects/mapbiomas-public/assets/brazil/lulc/collection11/mapbiomas_brazil_collection11_coverage_v3';
var mapbiomas = ee.Image(assetMapBiomas).clip(roi);
var mbAgua = mapbiomas.select('classification_2025').eq(33)
  .or(mapbiomas.select('classification_2024').eq(33))
  .or(mapbiomas.select('classification_2020').eq(33));

// C) Sentinel-2: MNDWI e Absorção SWIR (Água barrenta absorve SWIR fortemente)
function prepS2(img) {
  var qa = img.select('QA60');
  var nuvens = 1 << 10;
  var cirrus = 1 << 11;
  var maskQA = qa.bitwiseAnd(nuvens).eq(0).and(qa.bitwiseAnd(cirrus).eq(0));
  var scl = img.select('SCL');
  var maskSCL = scl.neq(3).and(scl.neq(8)).and(scl.neq(9)).and(scl.neq(10)).and(scl.neq(11));
  
  var clean = img.updateMask(maskQA.and(maskSCL));
  var ndvi = clean.normalizedDifference(['B8', 'B4']).rename('NDVI');
  // MNDWI usa SWIR1 (B11) que separa água barrenta de solo/vegetação com alta precisão
  var mndwi = clean.normalizedDifference(['B3', 'B11']).rename('MNDWI');
  return clean.addBands(ndvi).addBands(mndwi);
}

var s2Base = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(roi)
  .filter(ee.Filter.calendarRange(7, 11, 'month'))
  .map(prepS2);

var s2Inicial = s2Base.filterDate('2020-07-01', '2021-11-30').median().clip(roi);
var s2Recente = s2Base.filterDate('2024-07-01', '2025-11-30').median().clip(roi);

var ndviInicial = s2Inicial.select('NDVI');
var ndviRecente = s2Recente.select('NDVI');
var deltaNDVI = ndviRecente.subtract(ndviInicial).rename('delta_ndvi');
var mndwiRecente = s2Recente.select('MNDWI');
var swirRecente = s2Recente.select('B11');

// Água espectral no Sentinel-2 (MNDWI > -0.10 ou SWIR muito baixo < 500)
var s2Agua = mndwiRecente.gt(-0.10).or(swirRecente.lt(500));

// UNIÃO DE TODAS AS FONTES HÍDRICAS
var mascaraAguaTotal = jrcAgua.or(mbAgua).or(s2Agua);

// Buffer de proteção da margem fluvial (40m) para impedir invasão em bancos de lodo e orlas de maré
var bufferAgua = mascaraAguaTotal.focal_max({radius: 40, units: 'meters'});

Map.addLayer(mascaraAguaTotal.selfMask(), {palette: ['0000FF']}, 'Rios e Canais Hídricos (Máscara)', false);
Map.addLayer(bufferAgua.selfMask(), {palette: ['00FFFF']}, 'Buffer Fluvial de Exclusão (40m)', false);

// ------------------------------------------------------------------------------
// 3. IDENTIFICAÇÃO RIGOROSA DE ÁREAS TERRESTRES ELEGÍVEIS
// ------------------------------------------------------------------------------
// Piso mínimo de vegetação terrestre: NDVI >= 0.40 (abaixo disso é água barrenta ou lodo de maré)
var terraVegetada = ndviRecente.gte(0.40).and(bufferAgua.not());

// 1) Aberturas e mosaicos mapeados pelo MapBiomas (classes 11, 21, 25)
var mbAberto = mapbiomas.select('classification_2025').remap([11, 21, 25], [1, 1, 1], 0);

// 2) Dossel ralo / floresta de várzea degradada (0.40 <= NDVI < 0.70)
var dosselRalo = ndviRecente.gte(0.40).and(ndviRecente.lt(0.70)).and(terraVegetada);

var areasCandidatas = (mbAberto.eq(1).or(dosselRalo)).and(terraVegetada);

Map.addLayer(s2Recente, {bands: ['B4', 'B3', 'B2'], min: 200, max: 2000}, 'Sentinel-2 RGB Recente', false);
Map.addLayer(areasCandidatas.selfMask(), {palette: ['yellow']}, 'Áreas Terrestres Candidatas (Sem Rios)', false);

// ------------------------------------------------------------------------------
// 4. ESTRATIFICAÇÃO DOS MÉTODOS DE RESTAURAÇÃO
// ------------------------------------------------------------------------------
// 1 = Plantio Direto (degradação severa terrestre: 0.40 <= NDVI < 0.48 ou queda acentuada delta_ndvi < -0.10)
// 2 = Enriquecimento Florestal (dossel estagnado/raleado: 0.48 <= NDVI < 0.68)
// 3 = RNA (Regeneração Natural Assistida: ganho consistente delta_ndvi > 0.10 ou NDVI >= 0.68)
var classeRestauracao = ee.Image(0)
  .where(areasCandidatas.and(ndviRecente.lt(0.48).or(deltaNDVI.lt(-0.10))), 1)
  .where(areasCandidatas.and(
    (ndviRecente.gte(0.48).and(ndviRecente.lt(0.68)))
    .or(deltaNDVI.gte(-0.10).and(deltaNDVI.lte(0.10)))
  ), 2)
  .where(areasCandidatas.and(deltaNDVI.gt(0.10).or(ndviRecente.gte(0.68))), 3)
  .rename('classe_cod')
  .clip(roi);

var classeRestauracaoMasked = classeRestauracao.updateMask(areasCandidatas.and(classeRestauracao.gt(0)));

// ------------------------------------------------------------------------------
// 5. VETORIZAÇÃO DOS TALHÕES
// ------------------------------------------------------------------------------
var talhoesVetoriais = classeRestauracaoMasked.reduceToVectors({
  geometry: roi,
  crs: 'EPSG:31988',
  scale: 20,
  geometryType: 'polygon',
  eightConnected: true,
  labelProperty: 'classe_cod',
  maxPixels: 1e9
});

// Enriquecer atributos com tolerância de 1 metro na área
var talhoesProcessados = talhoesVetoriais.map(function(feat) {
  var areaHa = feat.geometry().area(1).divide(10000);
  var cod = ee.Number(feat.get('classe_cod'));
  
  var metodo = ee.Algorithms.If(
    cod.eq(3), 'RNA',
    ee.Algorithms.If(cod.eq(2), 'Enriquecimento', 'Plantio Direto')
  );

  var classeArea = ee.Algorithms.If(
    areaHa.lt(5), 'Pequeno (< 5 ha)',
    ee.Algorithms.If(
      areaHa.lt(20), 'Médio (5 - 20 ha)',
      ee.Algorithms.If(areaHa.lt(50), 'Grande (20 - 50 ha)', 'Macro-gleba (> 50 ha)')
    )
  );

  return feat.set({
    'id_talhao': feat.id(),
    'area_ha': areaHa,
    'metodo': metodo,
    'classe_area': classeArea,
    'uc': 'Parque Estadual Charapucu',
    'municipio': 'Afuá'
  });
}).filter(ee.Filter.gte('area_ha', 0.2));

// ------------------------------------------------------------------------------
// 6. VISUALIZAÇÃO TEMÁTICA
// ------------------------------------------------------------------------------
var talhoesRNA = talhoesProcessados.filter(ee.Filter.eq('metodo', 'RNA'));
var talhoesEnriq = talhoesProcessados.filter(ee.Filter.eq('metodo', 'Enriquecimento'));
var talhoesPlantio = talhoesProcessados.filter(ee.Filter.eq('metodo', 'Plantio Direto'));

Map.addLayer(talhoesRNA.style({color: '2ecc71', fillColor: '2ecc7188', width: 1}), {}, 'Talhões: RNA (Regeneração Natural Assistida)');
Map.addLayer(talhoesEnriq.style({color: 'f39c12', fillColor: 'f39c1288', width: 1}), {}, 'Talhões: Enriquecimento Florestal');
Map.addLayer(talhoesPlantio.style({color: 'e74c3c', fillColor: 'e74c3c88', width: 1}), {}, 'Talhões: Plantio Direto');

// ------------------------------------------------------------------------------
// 7. ESTATÍSTICAS NO CONSOLE
// ------------------------------------------------------------------------------
print('===========================================================');
print('🌳 BANCO DE RESTAURAÇÃO PES CHARAPUCU (SEM RIOS)');
print('===========================================================');
print('Total de Talhões Terrestres:', talhoesProcessados.size());
print('Área Total Filtrada (ha):', talhoesProcessados.aggregate_sum('area_ha'));

print('--- Estratificação por Método ---');
print('RNA (Regeneração Assistida):', talhoesRNA.size(), 'talhões | Área (ha):', talhoesRNA.aggregate_sum('area_ha'));
print('Enriquecimento Florestal   :', talhoesEnriq.size(), 'talhões | Área (ha):', talhoesEnriq.aggregate_sum('area_ha'));
print('Plantio Direto             :', talhoesPlantio.size(), 'talhões | Área (ha):', talhoesPlantio.aggregate_sum('area_ha'));
print('===========================================================');

// ------------------------------------------------------------------------------
// 8. EXPORTAÇÃO PARA O GOOGLE DRIVE
// ------------------------------------------------------------------------------
Export.table.toDrive({
  collection: talhoesProcessados,
  description: 'talhoes_restauracao_charapucu_geojson',
  folder: 'GEE_Charapucu',
  fileNamePrefix: 'talhoes_restauracao_charapucu',
  fileFormat: 'GeoJSON'
});

Export.table.toDrive({
  collection: talhoesProcessados,
  description: 'talhoes_restauracao_charapucu_shp',
  folder: 'GEE_Charapucu',
  fileNamePrefix: 'talhoes_restauracao_charapucu_shp',
  fileFormat: 'SHP'
});

Export.table.toDrive({
  collection: talhoesProcessados.select(['id_talhao', 'area_ha', 'metodo', 'classe_area', 'uc', 'municipio'], null, false),
  description: 'relatorio_talhoes_charapucu_csv',
  folder: 'GEE_Charapucu',
  fileNamePrefix: 'tabela_talhoes_charapucu',
  fileFormat: 'CSV'
});
