"""
Script: 00_extracao_limite_pes_charapucu.py
Descrição: Isola e valida o limite oficial do Parque Estadual Charapucu a partir
           da base de Unidades de Conservação Estaduais do Pará (DGMUC/IDEFLOR-Bio).
           Padroniza atributos para snake_case e converte geometrias para 2D.
"""

from pathlib import Path
import geopandas as gpd
from shapely import force_2d
from shapely.validation import make_valid
import yaml


def carregar_config(caminho_config: str = "config.yml") -> dict:
    with open(caminho_config, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def extrair_limite_charapucu():
    config = carregar_config()
    caminhos = config["caminhos"]
    cartografia = config["cartografia"]

    arquivo_ucs = Path(caminhos["limite_uc_raw"])
    if not arquivo_ucs.exists():
        raise FileNotFoundError(f"Arquivo de UCs não encontrado: {arquivo_ucs}")

    print(f"[1/5] Lendo base de UCs estaduais: {arquivo_ucs}...")
    gdf_ucs = gpd.read_file(arquivo_ucs)
    print(f"      Total de feições: {len(gdf_ucs)} | CRS original: {gdf_ucs.crs}")

    # Localizar a coluna de Nome e filtrar Parque Estadual Charapucu
    print("[2/5] Filtrando feição do Parque Estadual Charapucu...")
    col_nome = [c for c in gdf_ucs.columns if "nome" in c.lower()][0]
    mascara = gdf_ucs[col_nome].astype(str).str.contains("Charapucu", case=False, na=False)
    gdf_charapucu = gdf_ucs[mascara].copy()

    if gdf_charapucu.empty:
        raise ValueError("Parque Estadual Charapucu não foi localizado na base fornecida.")

    print(f"      Feição localizada com sucesso. Registros encontrados: {len(gdf_charapucu)}")

    # Padronização de nomes de colunas para snake_case seguro
    mapa_colunas = {}
    for col in gdf_charapucu.columns:
        c_low = col.lower()
        if "nome" in c_low:
            mapa_colunas[col] = "nome"
        elif "categoria" in c_low:
            mapa_colunas[col] = "categoria"
        elif "grupo" in c_low:
            mapa_colunas[col] = "grupo"
        elif "data" in c_low:
            mapa_colunas[col] = "data_criacao"
        elif "org" in c_low:
            mapa_colunas[col] = "orgao_gestor"
        elif "situa" in c_low:
            mapa_colunas[col] = "situacao_legal"
        elif "decreto" in c_low:
            mapa_colunas[col] = "area_decreto_ha"
        elif "municipio" in c_low:
            mapa_colunas[col] = "municipio"
        elif "integracao" in c_low or "regiao" in c_low:
            mapa_colunas[col] = "regiao_integracao"

    gdf_charapucu = gdf_charapucu.rename(columns=mapa_colunas)

    # Selecionar apenas colunas essenciais + geometry
    colunas_finais = [
        c for c in [
            "nome", "categoria", "grupo", "data_criacao", "orgao_gestor",
            "situacao_legal", "area_decreto_ha", "municipio", "regiao_integracao"
        ] if c in gdf_charapucu.columns
    ] + ["geometry"]

    gdf_charapucu = gdf_charapucu[colunas_finais].copy()

    # Garantir conversão para número em area_decreto_ha
    if "area_decreto_ha" in gdf_charapucu.columns:
        gdf_charapucu["area_decreto_ha"] = gdf_charapucu["area_decreto_ha"].astype(float)

    # Validação topológica e remoção de dimensão Z (force_2d)
    print("[3/5] Validando topologia e convertendo para 2D (force_2d)...")
    gdf_charapucu["geometry"] = gdf_charapucu["geometry"].apply(force_2d)
    gdf_charapucu["geometry"] = gdf_charapucu["geometry"].apply(make_valid)

    # Garantir que CRS está definido para EPSG:4674
    if gdf_charapucu.crs is None:
        gdf_charapucu.set_crs(cartografia["crs_geographic"], inplace=True)

    # Salvar limite bruto filtrado em GeoJSON (EPSG:4674)
    saida_geojson = Path(caminhos["limite_charapucu_geojson"])
    saida_geojson.parent.mkdir(parents=True, exist_ok=True)
    gdf_charapucu.to_file(saida_geojson, driver="GeoJSON")
    print(f"      Limite geográfico (EPSG:4674) salvo em: {saida_geojson}")

    # Reprojetar para CRS Métrico Oficial de Análise (SIRGAS 2000 / UTM zone 22N - EPSG:31988)
    print(f"[4/5] Reprojetando para o CRS Métrico de Trabalho: {cartografia['crs_metric']}...")
    gdf_charapucu_utm = gdf_charapucu.to_crs(cartografia["crs_metric"])

    # Cálculo da área métrica real em hectares
    area_m2 = gdf_charapucu_utm.geometry.area.sum()
    area_ha = area_m2 / 10000.0
    area_km2 = area_ha / 100.0
    area_decreto = float(gdf_charapucu["area_decreto_ha"].iloc[0]) if "area_decreto_ha" in gdf_charapucu.columns else 0.0

    gdf_charapucu_utm["area_calc_ha"] = area_ha
    gdf_charapucu_utm["perimetro_km"] = gdf_charapucu_utm.geometry.length.sum() / 1000.0

    # Salvar camada no data/processed em formato GeoPackage
    saida_gpkg = Path(caminhos["limite_charapucu_gpkg"])
    saida_gpkg.parent.mkdir(parents=True, exist_ok=True)
    gdf_charapucu_utm.to_file(saida_gpkg, layer="limite_pes_charapucu", driver="GPKG")
    print(f"      Limite métrico (EPSG:31988) salvo em: {saida_gpkg}")

    # Diagnóstico e Relatório Técnico
    print("\n" + "=" * 65)
    print("RELATÓRIO TÉCNICO DE EXTRAÇÃO — PES CHARAPUCU")
    print("=" * 65)
    print(f"Unidade de Conservação : {gdf_charapucu['nome'].iloc[0]}")
    print(f"Categoria / Grupo      : {gdf_charapucu.get('categoria', ['N/A']).iloc[0]} / {gdf_charapucu.get('grupo', ['N/A']).iloc[0]}")
    print(f"Município / RI         : {gdf_charapucu.get('municipio', ['N/A']).iloc[0]} / {gdf_charapucu.get('regiao_integracao', ['N/A']).iloc[0]}")
    print(f"Ato Legal de Criação   : {gdf_charapucu.get('situacao_legal', ['N/A']).iloc[0]} ({gdf_charapucu.get('data_criacao', ['N/A']).iloc[0]})")
    print(f"Órgão Gestor           : {gdf_charapucu.get('orgao_gestor', ['N/A']).iloc[0]}")
    print(f"Área de Decreto        : {area_decreto:,.2f} ha")
    print(f"Área Métrica Calculada : {area_ha:,.2f} ha ({area_km2:,.2f} km²)")
    print(f"Perímetro Calculado    : {gdf_charapucu_utm['perimetro_km'].iloc[0]:,.2f} km")
    delta_area = area_ha - area_decreto
    delta_perc = (delta_area / area_decreto) * 100.0 if area_decreto > 0 else 0
    print(f"Divergência Cartográfica: {delta_area:+.2f} ha ({delta_perc:+.3f}%)")
    bbox = gdf_charapucu.total_bounds
    print(f"Bounding Box (Geog)    : O={bbox[0]:.4f}, S={bbox[1]:.4f}, L={bbox[2]:.4f}, N={bbox[3]:.4f}")
    print(f"Geometria Válida?      : {gdf_charapucu_utm.geometry.is_valid.all()} (Tipo: {gdf_charapucu_utm.geometry.geom_type.iloc[0]})")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    extrair_limite_charapucu()
