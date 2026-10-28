"""
Script: 05_saneamento_fluvial_local.py
Descrição: Aplica filtro espacial rigoroso de afastamento fluvial (>= 50 metros)
           para eliminar 100% dos polígonos sobrepostos a rios, furos e bancos de lodo
           de maré, consolidando a carteira estritamente terrestre.
"""

from pathlib import Path
import json
import geopandas as gpd
import pandas as pd
import yaml


def sanear_carteira():
    with open("config.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    caminhos = config["caminhos"]
    cartografia = config["cartografia"]

    arquivo_geojson = Path("outputs/vetores/banco_restauracao_pes_charapucu.geojson")
    if not arquivo_geojson.exists():
        arquivo_geojson = Path("data/processed/banco_restauracao_consolidado.geojson")

    print(f"[1/4] Carregando carteira de: {arquivo_geojson}...")
    gdf = gpd.read_file(arquivo_geojson)
    total_inicial = len(gdf)
    area_inicial = gdf["area_ha"].sum()
    print(f"      Total bruto: {total_inicial} glebas | {area_inicial:.2f} ha")

    # 1. Filtro de Segurança Fluvial: Distância >= 50 metros da calha/margem externa
    print("[2/4] Aplicando buffer de recuo fluvial de 50 metros...")
    gdf_limpo = gdf[gdf["dist_margem_m"] >= 50.0].copy().reset_index(drop=True)
    removidos = total_inicial - len(gdf_limpo)
    area_removida = area_inicial - gdf_limpo["area_ha"].sum()
    print(f"      Glebas eliminadas na calha/orla de maré: {removidos} ({area_removida:.2f} ha)")
    print(f"      Glebas mantidas estritamente terrestres : {len(gdf_limpo)} ({gdf_limpo['area_ha'].sum():.2f} ha)")

    # 2. Re-classificar acessibilidade com recuo seguro
    def classificar_acesso_seguro(d):
        if d < 200.0:
            return "Alta (50 - 200 m)"
        elif d <= 800.0:
            return "Média (200 - 800 m)"
        else:
            return "Baixa (> 800 m)"

    gdf_limpo["acesso_fluvial"] = gdf_limpo["dist_margem_m"].apply(classificar_acesso_seguro)

    # Renumerar IDs de forma sequencial
    gdf_limpo["id_gleba"] = [f"GLEBA-{i+1:03d}" for i in range(len(gdf_limpo))]

    # 3. Exportar produtos vetoriais saneados
    print("[3/4] Atualizando camadas vetoriais sem corpos hídricos...")
    dir_vetores = Path(caminhos["outputs_vetores"])
    dir_relatorios = Path(caminhos["outputs_relatorios"])
    dir_vetores.mkdir(parents=True, exist_ok=True)
    dir_relatorios.mkdir(parents=True, exist_ok=True)

    # GeoPackage
    gpkg_out = dir_vetores / "banco_restauracao_pes_charapucu.gpkg"
    gdf_utm = gdf_limpo.to_crs(cartografia["crs_metric"])
    gdf_utm.to_file(gpkg_out, layer="carteira_completa_terrestre", driver="GPKG")

    gdf_alta = gdf_utm[gdf_utm["acesso_fluvial"] == "Alta (50 - 200 m)"].copy()
    if not gdf_alta.empty:
        gdf_alta.to_file(gpkg_out, layer="prioridade_alta_acessibilidade", driver="GPKG")

    # Limite oficial
    arquivo_limite = Path(caminhos["limite_charapucu_gpkg"])
    if arquivo_limite.exists():
        gdf_parque = gpd.read_file(arquivo_limite, layer="limite_pes_charapucu")
        gdf_parque.to_file(gpkg_out, layer="limite_pes_charapucu", driver="GPKG")

    # GeoJSON Web (EPSG:4326)
    geojson_out = dir_vetores / "banco_restauracao_pes_charapucu.geojson"
    gdf_wgs84 = gdf_limpo.to_crs(cartografia["crs_web"])
    gdf_wgs84.to_file(geojson_out, driver="GeoJSON")
    gdf_wgs84.to_file("data/processed/banco_restauracao_consolidado.geojson", driver="GeoJSON")
    gdf_wgs84.to_file("data/processed/talhoes_restauracao_charapucu.geojson", driver="GeoJSON")

    # 4. Atualizar relatórios analíticos
    print("[4/4] Atualizando relatórios executivos...")
    df_tabela = gdf_wgs84.drop(columns=["geometry"])
    df_tabela.to_csv(dir_relatorios / "tabela_geral_todas_glebas.csv", index=False, encoding="utf-8-sig")

    resumo_metodo = df_tabela.groupby("metodo").agg(
        qtd_talhoes=("id_gleba", "count"),
        area_total_ha=("area_ha", "sum"),
        area_media_ha=("area_ha", "mean"),
        dist_media_m=("dist_margem_m", "mean")
    ).round(2).reset_index()
    resumo_metodo.to_csv(dir_relatorios / "sintese_por_metodo.csv", index=False, encoding="utf-8-sig")

    resumo_acesso = df_tabela.groupby("acesso_fluvial").agg(
        qtd_talhoes=("id_gleba", "count"),
        area_total_ha=("area_ha", "sum"),
        dist_media_m=("dist_margem_m", "mean")
    ).round(2).reset_index()
    resumo_acesso.to_csv(dir_relatorios / "sintese_por_acessibilidade.csv", index=False, encoding="utf-8-sig")

    resumo_porte = df_tabela.groupby("classe_area").agg(
        qtd_talhoes=("id_gleba", "count"),
        area_total_ha=("area_ha", "sum")
    ).round(2).reset_index()
    resumo_porte.to_csv(dir_relatorios / "sintese_por_porte.csv", index=False, encoding="utf-8-sig")

    meta_base = config["projeto"]["meta_area_ha"]
    area_final = float(gdf_limpo["area_ha"].sum())
    resumo_executivo = {
        "projeto": config["projeto"]["nome"],
        "orgao": config["projeto"]["orgao"],
        "unidade_conservacao": config["projeto"]["unidade_conservacao"],
        "municipio": config["projeto"]["municipio"],
        "filtro_aplicado": "Exclusão total de rios e orlas de maré com recuo de segurança >= 50 metros",
        "meta_contratual_ha": meta_base,
        "area_total_inventariada_ha": round(area_final, 2),
        "superavit_ha": round(area_final - meta_base, 2),
        "percentual_meta_alcancado": round((area_final / meta_base) * 100.0, 1),
        "total_talhoes": len(gdf_limpo),
        "distancia_media_furos_m": round(float(gdf_limpo["dist_margem_m"].mean()), 1),
        "estratificacao_metodos": resumo_metodo.to_dict(orient="records"),
        "estratificacao_acesso": resumo_acesso.to_dict(orient="records"),
        "estratificacao_porte": resumo_porte.to_dict(orient="records")
    }

    with open(dir_relatorios / "resumo_executivo_carteira.json", "w", encoding="utf-8") as f:
        json.dump(resumo_executivo, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print("CARTEIRA PURIFICADA (SEM RIOS) — PES CHARAPUCU")
    print("=" * 70)
    print(f"Meta Básica Contratual      : {meta_base:.1f} ha")
    print(f"Área Terrestre Auditada     : {area_final:.2f} ha ({resumo_executivo['percentual_meta_alcancado']}% da meta)")
    print(f"Superávit Técnico Limpo     : +{resumo_executivo['superavit_ha']:.2f} ha")
    print(f"Total de Glebas Terrestres  : {len(gdf_limpo)} polígonos")
    print(f"Distância Média aos Furos   : {resumo_executivo['distancia_media_furos_m']} m")
    print("\n[Estratificação por Método]")
    for r in resumo_metodo.itertuples():
        perc = (r.area_total_ha / area_final) * 100.0
        print(f"  • {r.metodo:<22}: {r.qtd_talhoes:>3} talhões | {r.area_total_ha:>7.2f} ha ({perc:>5.1f}%) | Dist: {r.dist_media_m:.1f}m")
    print("\n[Estratificação por Acesso Fluvial]")
    for r in resumo_acesso.itertuples():
        perc = (r.area_total_ha / area_final) * 100.0
        print(f"  • {r.acesso_fluvial:<22}: {r.qtd_talhoes:>3} talhões | {r.area_total_ha:>7.2f} ha ({perc:>5.1f}%)")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    sanear_carteira()
