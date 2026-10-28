"""
Script: 03_estratificacao_talhoes.py
Descrição: Processa e consolida a carteira de talhões do PES Charapucu.
           - Calcula distância métrica aos furos/margens navegáveis (EPSG:31988).
           - Classifica acessibilidade fluvial (Alta, Média, Baixa).
           - Identifica setor fluvial mais próximo e calcula coordenadas centrais (Lat/Lon).
           - Padroniza identificadores operacionais (GLEBA-001, etc.).
           - Exporta produtos vetoriais (.gpkg, .geojson) e relatórios executivos (.csv, .json).
"""

from pathlib import Path
import json
import geopandas as gpd
import pandas as pd
from shapely.validation import make_valid
import yaml


def carregar_config(caminho_config: str = "config.yml") -> dict:
    with open(caminho_config, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def identificar_setor_fluvial(lon: float, lat: float) -> str:
    """
    Identifica o setor hidrográfico de referência ao redor da ilha do PES Charapucu
    com base nas coordenadas centrais do polígono.
    """
    # Centro aproximado da ilha: Lon -50.50, Lat -0.34
    if lat >= -0.26:
        return "Furo do Charapucu / Norte"
    elif lat <= -0.42:
        return "Rio Tajapuru / Furo dos Macacos (Sul)"
    elif lon <= -50.58:
        return "Rio Afuá / Oeste"
    elif lon >= -50.40:
        return "Baía do Vieira Grande / Leste"
    else:
        return "Canal Central / Interior da Ilha"


def processar_carteira():
    config = carregar_config()
    cartografia = config["cartografia"]
    caminhos = config["caminhos"]

    arquivo_talhoes = Path("data/processed/talhoes_restauracao_charapucu.geojson")
    arquivo_parque = Path(caminhos["limite_charapucu_gpkg"])

    if not arquivo_talhoes.exists():
        raise FileNotFoundError(f"Arquivo de talhões não encontrado: {arquivo_talhoes}")
    if not arquivo_parque.exists():
        raise FileNotFoundError(f"Arquivo do limite do parque não encontrado: {arquivo_parque}")

    print("[1/5] Carregando feições e limite oficial...")
    gdf_parque = gpd.read_file(arquivo_parque, layer="limite_pes_charapucu")
    gdf_talhoes_raw = gpd.read_file(arquivo_talhoes)
    print(f"      Talhões brutos carregados: {len(gdf_talhoes_raw)}")

    # Reprojetar para o CRS Métrico de Trabalho (SIRGAS 2000 / UTM zone 22N)
    print(f"[2/5] Reprojetando para métricas em {cartografia['crs_metric']}...")
    gdf_talhoes = gdf_talhoes_raw.to_crs(cartografia["crs_metric"]).copy()
    gdf_parque_utm = gdf_parque.to_crs(cartografia["crs_metric"]).copy()

    # Garantir geometrias válidas
    gdf_talhoes["geometry"] = gdf_talhoes["geometry"].apply(make_valid)

    # Recalcular área métrica precisa em hectares em UTM 22N
    gdf_talhoes["area_ha"] = (gdf_talhoes.geometry.area / 10000.0).round(2)

    # 1. Distância métrica à margem navegável (perímetro da ilha)
    print("[3/5] Calculando distâncias métricas às hidrovias e furos navegáveis...")
    margem_navegavel = gdf_parque_utm.geometry.boundary.iloc[0]
    gdf_talhoes["dist_margem_m"] = gdf_talhoes.geometry.distance(margem_navegavel).round(1)

    # 2. Classificação de Acessibilidade Fluvial
    def rotular_acesso(dist):
        if dist < 200.0:
            return "Alta (< 200 m)"
        elif dist <= 800.0:
            return "Média (200 - 800 m)"
        else:
            return "Baixa (> 800 m)"

    gdf_talhoes["acesso_fluvial"] = gdf_talhoes["dist_margem_m"].apply(rotular_acesso)

    # 3. Classificação de Porte / Classe de Área
    def rotular_porte(area):
        if area < 5.0:
            return "Pequeno (< 5 ha)"
        elif area < 20.0:
            return "Médio (5 - 20 ha)"
        elif area < 50.0:
            return "Grande (20 - 50 ha)"
        else:
            return "Macro-gleba (> 50 ha)"

    gdf_talhoes["classe_area"] = gdf_talhoes["area_ha"].apply(rotular_porte)

    # 4. Coordenadas centrais em SIRGAS 2000 Geográfico (EPSG:4674)
    gdf_centroids_geo = gdf_talhoes.geometry.centroid.to_crs(cartografia["crs_geographic"])
    gdf_talhoes["centroide_lon"] = gdf_centroids_geo.x.round(5)
    gdf_talhoes["centroide_lat"] = gdf_centroids_geo.y.round(5)

    # Setor fluvial mais próximo
    gdf_talhoes["setor_fluvial"] = [
        identificar_setor_fluvial(lon, lat)
        for lon, lat in zip(gdf_talhoes["centroide_lon"], gdf_talhoes["centroide_lat"])
    ]

    # Ordenar por método e área decrescente e gerar IDs operacionais
    gdf_talhoes = gdf_talhoes.sort_values(by=["area_ha"], ascending=False).reset_index(drop=True)
    gdf_talhoes["id_gleba"] = [f"GLEBA-{i+1:03d}" for i in range(len(gdf_talhoes))]

    # Selecionar colunas finais estruturadas
    colunas_ordenadas = [
        "id_gleba",
        "metodo",
        "area_ha",
        "classe_area",
        "acesso_fluvial",
        "dist_margem_m",
        "setor_fluvial",
        "centroide_lat",
        "centroide_lon",
        "uc",
        "municipio",
        "geometry"
    ]
    gdf_consolidado = gdf_talhoes[colunas_ordenadas].copy()

    # 5. Exportação dos produtos vetoriais
    print("[4/5] Exportando produtos vetoriais estruturados...")
    dir_vetores = Path(caminhos["outputs_vetores"])
    dir_relatorios = Path(caminhos["outputs_relatorios"])
    dir_vetores.mkdir(parents=True, exist_ok=True)
    dir_relatorios.mkdir(parents=True, exist_ok=True)

    # GeoPackage com camadas de carteira total e alta acessibilidade
    gpkg_saida = dir_vetores / "banco_restauracao_pes_charapucu.gpkg"
    gdf_consolidado.to_file(gpkg_saida, layer="carteira_completa", driver="GPKG")
    
    # Camada isolada de alta acessibilidade (< 200 m)
    gdf_alta = gdf_consolidado[gdf_consolidado["acesso_fluvial"] == "Alta (< 200 m)"].copy()
    gdf_alta.to_file(gpkg_saida, layer="prioridade_alta_acessibilidade", driver="GPKG")

    # Limite oficial da UC no mesmo GPKG para facilitar projetos SIG
    gdf_parque_utm.to_file(gpkg_saida, layer="limite_pes_charapucu", driver="GPKG")
    print(f"      GeoPackage consolidado salvo em: {gpkg_saida}")

    # GeoJSON em WGS 84 (EPSG:4326) para o Dashboard Web
    geojson_saida = dir_vetores / "banco_restauracao_pes_charapucu.geojson"
    gdf_consolidado.to_crs(cartografia["crs_web"]).to_file(geojson_saida, driver="GeoJSON")
    print(f"      GeoJSON para Web salvo em: {geojson_saida}")

    # Também salvar uma cópia em data/processed para consumo rápido
    gdf_consolidado.to_crs(cartografia["crs_web"]).to_file(
        "data/processed/banco_restauracao_consolidado.geojson", driver="GeoJSON"
    )

    # 6. Relatórios Analíticos Consolidados
    print("[5/5] Gerando relatórios tabulares e resumo executivo...")
    df_tabela = gdf_consolidado.drop(columns=["geometry"])
    df_tabela.to_csv(dir_relatorios / "tabela_geral_todas_glebas.csv", index=False, encoding="utf-8-sig")

    # Síntese por Método
    resumo_metodo = df_tabela.groupby("metodo").agg(
        qtd_talhoes=("id_gleba", "count"),
        area_total_ha=("area_ha", "sum"),
        area_media_ha=("area_ha", "mean"),
        dist_media_m=("dist_margem_m", "mean")
    ).round(2).reset_index()
    resumo_metodo.to_csv(dir_relatorios / "sintese_por_metodo.csv", index=False, encoding="utf-8-sig")

    # Síntese por Acessibilidade
    resumo_acesso = df_tabela.groupby("acesso_fluvial").agg(
        qtd_talhoes=("id_gleba", "count"),
        area_total_ha=("area_ha", "sum"),
        dist_media_m=("dist_margem_m", "mean")
    ).round(2).reset_index()
    resumo_acesso.to_csv(dir_relatorios / "sintese_por_acessibilidade.csv", index=False, encoding="utf-8-sig")

    # Síntese por Classe de Porte
    resumo_porte = df_tabela.groupby("classe_area").agg(
        qtd_talhoes=("id_gleba", "count"),
        area_total_ha=("area_ha", "sum")
    ).round(2).reset_index()
    resumo_porte.to_csv(dir_relatorios / "sintese_por_porte.csv", index=False, encoding="utf-8-sig")

    # Resumo Executivo em JSON
    meta_base = config["projeto"]["meta_area_ha"]
    area_total = float(gdf_consolidado["area_ha"].sum())
    resumo_executivo = {
        "projeto": config["projeto"]["nome"],
        "orgao": config["projeto"]["orgao"],
        "unidade_conservacao": config["projeto"]["unidade_conservacao"],
        "municipio": config["projeto"]["municipio"],
        "meta_contratual_ha": meta_base,
        "area_total_inventariada_ha": round(area_total, 2),
        "superavit_ha": round(area_total - meta_base, 2),
        "percentual_meta_alcancado": round((area_total / meta_base) * 100.0, 1),
        "total_talhoes": len(gdf_consolidado),
        "distancia_media_furos_m": round(float(gdf_consolidado["dist_margem_m"].mean()), 1),
        "estratificacao_metodos": resumo_metodo.to_dict(orient="records"),
        "estratificacao_acesso": resumo_acesso.to_dict(orient="records"),
        "estratificacao_porte": resumo_porte.to_dict(orient="records")
    }

    with open(dir_relatorios / "resumo_executivo_carteira.json", "w", encoding="utf-8") as f:
        json.dump(resumo_executivo, f, ensure_ascii=False, indent=2)

    # Imprimir Relatório Técnico Final
    print("\n" + "=" * 70)
    print("RESUMO EXECUTIVO DA CARTEIRA AUDITADA — PES CHARAPUCU")
    print("=" * 70)
    print(f"Meta Básica Contratual      : {meta_base:.1f} ha")
    print(f"Área Total Inventariada     : {area_total:.2f} ha ({resumo_executivo['percentual_meta_alcancado']}% da meta)")
    print(f"Superávit Técnico Estratégico: +{resumo_executivo['superavit_ha']:.2f} ha excedentes")
    print(f"Número Total de Glebas      : {len(gdf_consolidado)} talhões auditados")
    print(f"Distância Média aos Furos   : {resumo_executivo['distancia_media_furos_m']} m")
    print("\n[Detalhamento por Método de Restauração]")
    for row in resumo_metodo.itertuples():
        perc = (row.area_total_ha / area_total) * 100.0
        print(f"  • {row.metodo:<22}: {row.qtd_talhoes:>3} talhões | {row.area_total_ha:>7.2f} ha ({perc:>5.1f}%) | Dist. Média: {row.dist_media_m:.1f} m")
    print("\n[Detalhamento por Acessibilidade Fluvial]")
    for row in resumo_acesso.itertuples():
        perc = (row.area_total_ha / area_total) * 100.0
        print(f"  • {row.acesso_fluvial:<22}: {row.qtd_talhoes:>3} talhões | {row.area_total_ha:>7.2f} ha ({perc:>5.1f}%)")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    processar_carteira()
