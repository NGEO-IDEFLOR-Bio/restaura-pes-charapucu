"""
Script de Execução do Layout QGIS em Python (src/07_gerar_mapa_layout_qgis.py)
Aplica a arquitetura cartográfica de 3 mapas do QGIS para o Parque Estadual Charapucu.
"""

import os
import geopandas as gpd
from qgis_layout_engine import QGISLayoutEngine

def main():
    print("=" * 70)
    print("GERADOR DE LAYOUT CARTOGRÁFICO QGIS (NGEO/IDEFLOR-BIO)")
    print("=" * 70)

    # 1. Definição de caminhos
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    qgis_dir = r"H:\Meu Drive\DEV\layout_extraido_qgis"
    tutorial_dir = r"H:\Meu Drive\DEV\pyqgis-location-map-tutorial\dados"

    path_layout_json = os.path.join(qgis_dir, "layout_elements.json")
    path_alvo = os.path.join(base_dir, "outputs", "vetores", "banco_restauracao_pes_charapucu.geojson")
    path_ucs = os.path.join(qgis_dir, "data", "ucs_estaduais.geojson")
    path_municipios = os.path.join(qgis_dir, "data", "municipios.geojson")
    path_estados = os.path.join(tutorial_dir, "estados_brasileiros.shp")
    path_ams = os.path.join(tutorial_dir, "america_do_sul.shp")

    path_logo_ngeo = os.path.join(qgis_dir, "assets", "img", "logo-ngeo.png")
    path_logo_ideflor = os.path.join(qgis_dir, "assets", "img", "logo-ideflor-bio.png")
    path_logo_gov = os.path.join(qgis_dir, "assets", "img", "brasao-para.png")

    out_png = os.path.join(base_dir, "outputs", "mapas", "mapa_layout_qgis_deter_charapucu.png")
    out_pdf = os.path.join(base_dir, "outputs", "mapas", "mapa_layout_qgis_deter_charapucu.pdf")

    # 2. Carregamento dos dados espaciais
    print("\n[1/5] Carregando camadas vetoriais...")
    gdf_alvo = gpd.read_file(path_alvo)
    print(f"  • Áreas auditadas (DETER): {len(gdf_alvo)} feições ({gdf_alvo['area_ha'].sum():.2f} ha)")

    gdf_ucs_all = gpd.read_file(path_ucs)
    gdf_uc = gdf_ucs_all[gdf_ucs_all["Nome"] == "Parque Estadual Charapucu"]
    print(f"  • Limite da UC carregado: {gdf_uc['Nome'].iloc[0]}")

    gdf_municipios = gpd.read_file(path_municipios)
    gdf_afua = gdf_municipios[gdf_municipios["Município [-]"].str.contains("Afu", case=False, na=False)]
    if len(gdf_afua) == 0:
        gdf_afua = gdf_municipios[gdf_municipios["MUNICÍPIO"].str.contains("Afu", case=False, na=False)]
    print(f"  • Contexto municipal: {len(gdf_afua)} feição encontrada")

    gdf_estados = gpd.read_file(path_estados)
    print(f"  • Estados brasileiros carregados: {len(gdf_estados)}")

    gdf_paises = gpd.read_file(path_ams)
    print(f"  • América do Sul carregada: {len(gdf_paises)} países")

    # 3. Inicialização do Motor de Layout
    print("\n[2/5] Inicializando prancha A4 Paisagem (297 x 210 mm)...")
    engine = QGISLayoutEngine(path_layout_json)
    engine.create_layout()
    engine.draw_frames()

    # 4. Renderização dos Títulos e Metadados
    print("[3/5] Inserindo cabeçalhos, logos e notas cartográficas...")
    engine.draw_header_and_titles(
        titulo_mapa="MAPA DE DIAGNÓSTICO DE DESMATAMENTO (DETER / INPE) – PARQUE ESTADUAL CHARAPUCU",
        subtitulo_unidade="PARQUE ESTADUAL CHARAPUCU"
    )
    engine.draw_metadata_and_sources()
    engine.draw_logos(path_logo_ngeo, path_logo_ideflor, path_logo_gov)
    engine.draw_north_arrow()

    # 5. Renderização dos Três Mapas Cartográficos
    print("\n[4/5] Renderizando os 3 níveis da hierarquia cartográfica:")
    print("  -> Nível 1: Renderizando Mapa Macro (Contexto do Estado do Pará e Vizinhos)...")
    engine.render_macro_map(gdf_estados, gdf_paises, gdf_uc)

    print("  -> Nível 2: Renderizando Mapa Intermediário (Enquadramento no PES Charapucu)...")
    engine.render_intermediate_map(gdf_uc, gdf_alvo, gdf_afua)

    print("  -> Nível 3: Renderizando Mapa Principal (Zoom com Mosaico Sentinel-2 EOX)...")
    engine.render_main_map(gdf_alvo, eox_year="2025")

    # 6. Renderização da Legenda e Exportação
    print("\n[5/5] Finalizando legenda e gravando arquivos de alta resolução...")
    engine.render_legend()
    engine.export(out_png, out_pdf, dpi=300)

    print("\n" + "=" * 70)
    print("PROCESSO CONCLUÍDO COM SUCESSO!")
    print(f"PNG: {out_png}")
    print(f"PDF: {out_pdf}")
    print("=" * 70)

if __name__ == "__main__":
    main()
