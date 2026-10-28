/**
 * ==============================================================================
 * PROJETO: Banco de Áreas Elegíveis para Restauração Florestal — PES Charapucu
 * ÓRGÃO: Núcleo de Geotecnologias (NGEO) / IDEFLOR-Bio
 * AMBIENTE: Google Earth Engine (GEE Code Editor)
 * ==============================================================================
 * VERSÃO 2.0 (CALIBRAÇÃO ECOLÓGICA PARA VÁRZEA ESTUARINA):
 * - Preserva a floresta contínua de várzea (NDVI >= 0.55) como ecossistema íntegro.
 * - Elimina falsos positivos em canais d'água e igarapés estreitos (MNDWI > -0.16 e SWIR < 650).
 * - Identifica exclusivamente clareiras reais, quedas de dossel (delta_NDVI < -0.10)
 *   e regenerações comprovadas (delta_NDVI > +0.10) ou histórico antrópico MapBiomas.
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
// 2. MÁSCARA HÍDRICA MULTIFONTE DE ALTA SENSIBILIDADE
// ------------------------------------------------------------------------------
// A) JRC Global Surface Water (Histórico de 38 anos)
var jrc = ee.Image('JRC/GSW1_4/GlobalSurfaceWater').clip(roi);
var jrcAgua = jrc.select('occurrence').gt(5).or(jrc.select('max_extent').eq(1));

// B) MapBiomas Coleção 11 - Classe 33 (Corpos d'Água)
var assetMapBiomas = 'projects/mapbiomas-public/assets/brazil/lulc/collection11/mapbiomas_brazil_collection11_coverage_v3';
var mapbiomas = ee.Image(assetMapBiomas).clip(roi);
var mbAgua = mapbiomas.select('classification_2025').eq(33)
  .or(mapbiomas.select('classification_2024').eq(33))
  .or(mapbiomas.select('classification_2020').eq(33));

// C) Sentinel-2: Pré-processamento e Índices Espectrais
function prepS2(img) {
  var qa = img.select('QA60');
  var nuvens = 1 << 10;
  var cirrus = 1 << 11;
  var maskQA = qa.bitwiseAnd(nuvens).eq(0).and(qa.bitwiseAnd(cirrus).eq(0));
  var scl = img.select('SCL');
  var maskSCL = scl.neq(3).and(scl.neq(8)).and(scl.neq(9)).and(scl.neq(10)).and(scl.neq(11));
  
  var clean = img.updateMask(maskQA.and(maskSCL));
  var ndvi = clean.normalizedDifference(['B8', 'B4']).rename('NDVI');
  // MNDWI: Green (B3) e SWIR1 (B11) — máxima sensibilidade a água e solo lamacento
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

// D) Detecção estrita de água e igarapés estreitos de maré:
// MNDWI > -0.16 OU SWIR < 650 detecta canais fluviais e poças de maré subpixel
var s2Agua = mndwiRecente.gt(-0.16).or(swirRecente.lt(650));

// UNIÃO DAS MÁSCARAS HÍDRICAS + Buffer estrito de 50 metros
var mascaraAguaTotal = jrcAgua.or(mbAgua).or(s2Agua);
var bufferAgua = mascaraAguaTotal.focal_max({radius: 50, units: 'meters'});

Map.addLayer(mascaraAguaTotal.selfMask(), {palette: ['0000FF']}, 'Canais Hídricos e Igarapés', false);
Map.addLayer(bufferAgua.selfMask(), {palette: ['00FFFF']}, 'Buffer Fluvial de Exclusão (50m)', false);

// ------------------------------------------------------------------------------
// 3. IDENTIFICAÇÃO ECOLÓGICA DE ÁREAS REALMENTE ELEGÍVEIS (VÁRZEA ESTUARINA)
// ------------------------------------------------------------------------------
// Piso de vegetação terrestre (elimina praias de lama/maré e sedimento líquido)
var terraSeca = ndviRecente.gte(0.28).and(mndwiRecente.lt(-0.16)).and(bufferAgua.not());

// 1) Histórico antrópico / aberturas do MapBiomas (classes 15=pastagem, 21=mosaico, 25=não vegetado)
var mbAberto = mapbiomas.select('classification_2025').remap([15, 21, 25], [1, 1, 1], 0);

// 2) Clareiras reais / Dossel aberto (NDVI < 0.48): áreas abertas sem dossel contínuo
var clareiraAberta = ndviRecente.gte(0.28).and(ndviRecente.lt(0.48)).and(terraSeca);

// 3) Perda multitemporal evidente de dossel (delta_NDVI < -0.10)
var perdaDossel = deltaNDVI.lt(-0.10).and(terraSeca);

// 4) Regeneração natural ativa comprovada (delta_NDVI > +0.10 partindo de clareira)
var ganhoRegenerativo = deltaNDVI.gt(0.10).and(ndviInicial.lt(0.60)).and(terraSeca);

// ÁREAS CANDIDATAS REAIS (Sem sobreposição à floresta de várzea íntegra nem a canais de água)
var areasCandidatas = (mbAberto.eq(1).or(clareiraAberta).or(perdaDossel).or(ganhoRegenerativo)).and(terraSeca);

Map.addLayer(s2Recente, {bands: ['B4', 'B3', 'B2'], min: 200, max: 2000}, 'Sentinel-2 RGB Recente', false);
Map.addLayer(areasCandidatas.selfMask(), {palette: ['yellow']}, 'Clareiras Candidatas (Sem Rios)', false);

// ------------------------------------------------------------------------------
// 4. ESTRATIFICAÇÃO DOS MÉTODOS DE RESTAURAÇÃO
// ------------------------------------------------------------------------------
// 1 = Plantio Direto (clareiras severas: NDVI < 0.45 ou perda acentuada delta_ndvi < -0.12)
// 2 = Enriquecimento Florestal (dossel intermediário em bordas de clareira: 0.45 <= NDVI < 0.55 ou mosaico)
// 3 = RNA (Regeneração Natural Assistida: ganho consistente delta_ndvi > 0.10)
var classeRestauracao = ee.Image(0)
  .where(areasCandidatas.and(ndviRecente.lt(0.45).or(deltaNDVI.lt(-0.12))), 1)
  .where(areasCandidatas.and(
    (ndviRecente.gte(0.45).and(ndviRecente.lt(0.55)))
    .or(mbAberto.eq(1))
  ), 2)
  .where(areasCandidatas.and(deltaNDVI.gte(0.10)), 3)
  .rename('classe_cod')
  .clip(roi);

var classeRestauracaoMasked = classeRestauracao.updateMask(areasCandidatas.and(classeRestauracao.gt(0)));

// ------------------------------------------------------------------------------
// 5. VETORIZAÇÃO E FILTRAGEM GEOMÉTRICA
// ------------------------------------------------------------------------------
var talhoesVetoriais = classeRestauracaoMasked.reduceToVectors({
  geometry: roi,
  crs: 'EPSG:31988',
  scale: 15,
  geometryType: 'polygon',
  eightConnected: true,
  labelProperty: 'classe_cod',
  maxPixels: 1e9
});

// Enriquecer atributos e filtrar área mínima (>= 0.25 ha)
var talhoesProcessados = talhoesVetoriais.map(function(feat) {
  var areaHa = feat.geometry().area(1).divide(10000);
  var cod = ee.Number(feat.get('classe_cod'));
  
  var diagnostico = ee.Algorithms.If(
    cod.eq(3), 'Regeneração em Curso',
    ee.Algorithms.If(cod.eq(2), 'Dossel Ralo / Alteração Moderada', 'Clareira Aberta / Baixa Biomassa')
  );

  var severidade = ee.Algorithms.If(
    cod.eq(3), 'Baixa / Recuperação',
    ee.Algorithms.If(cod.eq(2), 'Moderada', 'Alta')
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
    'diagnostico': diagnostico,
    'severidade': severidade,
    'classe_area': classeArea,
    'uc': 'Parque Estadual Charapucu',
    'municipio': 'Afuá'
  });
}).filter(ee.Filter.gte('area_ha', 0.25));

// ------------------------------------------------------------------------------
// 6. VISUALIZAÇÃO TEMÁTICA DE DIAGNÓSTICO
// ------------------------------------------------------------------------------
var talhoesRegen = talhoesProcessados.filter(ee.Filter.eq('diagnostico', 'Regeneração em Curso'));
var talhoesDossel = talhoesProcessados.filter(ee.Filter.eq('diagnostico', 'Dossel Ralo / Alteração Moderada'));
var talhoesClareira = talhoesProcessados.filter(ee.Filter.eq('diagnostico', 'Clareira Aberta / Baixa Biomassa'));

Map.addLayer(talhoesRegen.style({color: '2ecc71', fillColor: '2ecc71aa', width: 1.5}), {}, 'Diagnóstico: Regeneração em Curso');
Map.addLayer(talhoesDossel.style({color: 'f39c12', fillColor: 'f39c12aa', width: 1.5}), {}, 'Diagnóstico: Dossel Ralo / Moderada');
Map.addLayer(talhoesClareira.style({color: 'e74c3c', fillColor: 'e74c3caa', width: 1.5}), {}, 'Diagnóstico: Clareira Aberta (Alta)');

// ------------------------------------------------------------------------------
// 7. ESTATÍSTICAS NO CONSOLE
// ------------------------------------------------------------------------------
print('===========================================================');
print('DIAGNÓSTICO GEOESPACIAL DE COBERTURA — PES CHARAPUCU');
print('===========================================================');
print('Total de Glebas Terrestres:', talhoesProcessados.size());
print('Área Total Diagnosticada (ha):', talhoesProcessados.aggregate_sum('area_ha'));

print('--- Estratificação por Diagnóstico ---');
print('Regeneração em Curso            :', talhoesRegen.size(), 'glebas | Área (ha):', talhoesRegen.aggregate_sum('area_ha'));
print('Dossel Ralo / Alteração Moderada:', talhoesDossel.size(), 'glebas | Área (ha):', talhoesDossel.aggregate_sum('area_ha'));
print('Clareira Aberta / Baixa Biomassa:', talhoesClareira.size(), 'glebas | Área (ha):', talhoesClareira.aggregate_sum('area_ha'));
print('===========================================================');

// ------------------------------------------------------------------------------
// 8. EXPORTAÇÃO PARA O GOOGLE DRIVE
// ------------------------------------------------------------------------------
Export.table.toDrive({
  collection: talhoesProcessados,
  description: 'diagnostico_cobertura_charapucu_geojson',
  folder: 'GEE_Charapucu',
  fileNamePrefix: 'diagnostico_cobertura_charapucu',
  fileFormat: 'GeoJSON'
});

Export.table.toDrive({
  collection: talhoesProcessados,
  description: 'diagnostico_cobertura_charapucu_shp',
  folder: 'GEE_Charapucu',
  fileNamePrefix: 'diagnostico_cobertura_charapucu_shp',
  fileFormat: 'SHP'
});

Export.table.toDrive({
  collection: talhoesProcessados.select(['id_talhao', 'area_ha', 'diagnostico', 'severidade', 'classe_area', 'uc', 'municipio'], null, false),
  description: 'relatorio_diagnostico_charapucu_csv',
  folder: 'GEE_Charapucu',
  fileNamePrefix: 'tabela_diagnostico_charapucu',
  fileFormat: 'CSV'
});
