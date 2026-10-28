"""
Script: 06_consolidar_deter_charapucu.py
Descrição: Consolida a carteira auditada de diagnóstico florestal no PES Charapucu
           baseada estritamente nos dados oficiais de corte raso do DETER (INPE / TerraBrasilis).
"""

from pathlib import Path
import json
import geopandas as gpd
import pandas as pd
import pandas.api.types as ptypes
import yaml


def processar_deter():
    with open("config.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    cartografia = config["cartografia"]
    caminhos = config["caminhos"]

    arquivo_deter = Path("data/raw/deter_alertas_charapucu.geojson")
    arquivo_parque = Path(caminhos["limite_charapucu_gpkg"])

    print(f"[1/4] Carregando dados oficiais do DETER e limite oficial...")
    gdf_deter = gpd.read_file(arquivo_deter)
    gdf_parque = gpd.read_file(arquivo_parque, layer="limite_pes_charapucu")

    # Reprojetar para UTM 22N
    gdf_deter_utm = gdf_deter.to_crs(cartografia["crs_metric"]).copy()
    gdf_parque_utm = gdf_parque.to_crs(cartografia["crs_metric"]).copy()

    # Cálculo métrico exato
    margem = gdf_parque_utm.geometry.boundary.iloc[0]
    gdf_deter_utm["area_ha"] = (gdf_deter_utm.geometry.area / 10000.0).round(2)
    gdf_deter_utm["dist_margem_m"] = gdf_deter_utm.geometry.distance(margem).round(1)

    # Ordenar por área decrescente
    gdf_deter_utm = gdf_deter_utm.sort_values("area_ha", ascending=False).reset_index(drop=True)

    # Atributos padronizados
    ids = [f"GLEBA-DETER-{i+1:02d}" for i in range(len(gdf_deter_utm))]
    gdf_deter_utm["id_gleba"] = ids
    gdf_deter_utm["id_inpe"] = gdf_deter_utm["gid"]
    gdf_deter_utm["fonte"] = "DETER / INPE (TerraBrasilis)"
    gdf_deter_utm["classe_inpe"] = gdf_deter_utm["classname"]
    gdf_deter_utm["data_alerta"] = gdf_deter_utm["view_date"].astype(str).str[:10]
    gdf_deter_utm["diagnostico"] = "Corte Raso Oficial em Regeneração Secundária"
    gdf_deter_utm["severidade"] = "Histórica (2019) / Alta Prioridade de Manejo"

    def classificar_porte(a):
        if a >= 50.0:
            return "Macro-gleba (> 50 ha)"
        elif a >= 20.0:
            return "Grande (20 - 50 ha)"
        elif a >= 5.0:
            return "Médio (5 - 20 ha)"
        else:
            return "Pequeno (< 5 ha)"

    gdf_deter_utm["classe_area"] = gdf_deter_utm["area_ha"].apply(classificar_porte)

    def classificar_acesso(d):
        if d <= 200.0:
            return "Alta (50 - 200 m)"
        elif d <= 800.0:
            return "Média (200 - 800 m)"
        else:
            return "Baixa (> 800 m - Interior)"

    gdf_deter_utm["acesso_fluvial"] = gdf_deter_utm["dist_margem_m"].apply(classificar_acesso)
    gdf_deter_utm["setor_fluvial"] = "Baía de Vieira Grande / Setor Leste"
    gdf_deter_utm["uc"] = "Parque Estadual Charapucu"
    gdf_deter_utm["municipio"] = "Afuá"

    # Coordenadas SIRGAS 2000
    gdf_geo = gdf_deter_utm.to_crs(cartografia["crs_geographic"])
    gdf_deter_utm["centroide_lat"] = gdf_geo.geometry.centroid.y.round(5)
    gdf_deter_utm["centroide_lon"] = gdf_geo.geometry.centroid.x.round(5)

    colunas = [
        "id_gleba", "id_inpe", "fonte", "classe_inpe", "data_alerta",
        "diagnostico", "severidade", "area_ha", "classe_area",
        "dist_margem_m", "acesso_fluvial", "setor_fluvial",
        "centroide_lat", "centroide_lon", "uc", "municipio", "geometry"
    ]

    gdf_export_utm = gdf_deter_utm[colunas].copy()

    # Garantir que nenhum campo seja datetime/Timestamp para evitar erros de serialização GeoJSON/Folium
    for col in gdf_export_utm.columns:
        if ptypes.is_datetime64_any_dtype(gdf_export_utm[col]):
            gdf_export_utm[col] = gdf_export_utm[col].astype(str)
    gdf_export_utm["data_alerta"] = gdf_export_utm["data_alerta"].astype(str)

    # Exportar GPKG
    print("[2/4] Exportando GeoPackage e GeoJSON oficial...")
    dir_vetores = Path(caminhos["outputs_vetores"])
    dir_relatorios = Path(caminhos["outputs_relatorios"])
    dir_vetores.mkdir(parents=True, exist_ok=True)
    dir_relatorios.mkdir(parents=True, exist_ok=True)

    gpkg_out = dir_vetores / "banco_restauracao_pes_charapucu.gpkg"
    gdf_export_utm.to_file(gpkg_out, layer="carteira_completa_terrestre", driver="GPKG")
    gdf_export_utm.to_file(gpkg_out, layer="alertas_deter_oficial", driver="GPKG")
    gdf_parque_utm.to_file(gpkg_out, layer="limite_pes_charapucu", driver="GPKG")

    # GeoJSON Web (EPSG:4326)
    gdf_wgs84 = gdf_export_utm.to_crs("EPSG:4326")
    geojson_out = dir_vetores / "banco_restauracao_pes_charapucu.geojson"
    gdf_wgs84.to_file(geojson_out, driver="GeoJSON")
    gdf_wgs84.to_file("data/processed/banco_restauracao_consolidado.geojson", driver="GeoJSON")
    gdf_wgs84.to_file("data/processed/talhoes_restauracao_charapucu.geojson", driver="GeoJSON")

    # Relatórios
    print("[3/4] Atualizando relatórios executivos...")
    df_tab = gdf_wgs84.drop(columns=["geometry"])
    df_tab.to_csv(dir_relatorios / "tabela_geral_todas_glebas.csv", index=False, encoding="utf-8-sig")

    meta_base = config["projeto"]["meta_area_ha"]
    area_total = float(gdf_export_utm["area_ha"].sum())
    superavit = area_total - meta_base

    resumo = {
        "projeto": "Diagnóstico Geoespacial de Corte Raso Oficial (DETER/INPE) — PES Charapucu",
        "orgao": config["projeto"]["orgao"],
        "unidade_conservacao": config["projeto"]["unidade_conservacao"],
        "municipio": config["projeto"]["municipio"],
        "fonte_primaria": "DETER - Amazônia Legal (INPE / TerraBrasilis)",
        "classe_oficial": "DESMATAMENTO_CR (Desmatamento por Corte Raso)",
        "data_deteccao_inpe": "2019-07-20",
        "meta_contratual_ha": meta_base,
        "area_total_auditada_ha": round(area_total, 2),
        "superavit_ha": round(superavit, 2),
        "percentual_meta_alcancado": round((area_total / meta_base) * 100.0, 1),
        "total_poligonos": len(gdf_export_utm),
        "detalhe_glebas": df_tab.to_dict(orient="records")
    }

    with open(dir_relatorios / "resumo_executivo_carteira.json", "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print("CARTEIRA OFICIAL DETER/INPE CONSOLIDADA — PES CHARAPUCU")
    print("=" * 70)
    print(f"Meta Básica Contratual      : {meta_base:.1f} ha")
    print(f"Área Oficial Auditada       : {area_total:.2f} ha ({resumo['percentual_meta_alcancado']}% da meta)")
    print(f"Superávit Consolidado       : +{superavit:.2f} ha")
    print(f"Total de Polígonos Oficiais : {len(gdf_export_utm)} glebas contíguas")
    for r in df_tab.itertuples():
        print(f"  • {r.id_gleba} ({r.id_inpe}): {r.area_ha:.2f} ha | Data: {r.data_alerta} | Dist. Furos: {r.dist_margem_m:.1f}m")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    processar_deter()
