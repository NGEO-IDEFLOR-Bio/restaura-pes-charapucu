"""
Motor Cartográfico QGIS para Python / Colab (qgis_layout_engine.py)
Reproduz com fidelidade milimétrica e conformidade técnica o layout A4 Paisagem (297 x 210 mm)
do Núcleo de Geotecnologias (NGEO/IDEFLOR-Bio).

Diretrizes Técnicas de Correção Aplicadas:
1. Enquadramento e Extensão do Mapa Principal:
   - Viewport 100% preenchida sem moldura interna preta/vazia nem faixas residuais.
   - Grade de coordenadas e ticks ancorados diretamente nos limites da área visível.
2. Caixa de Texto do Rodapé (Fontes e Metadados):
   - Controle estrito de largura de linha para evitar colisão com os logos à direita.
   - Recuo inferior suficiente para não colidir com o traço divisório da prancha.
3. Restauração das Coordenadas no Mapa de Localização Superior:
   - Grade e rótulos de coordenadas restabelecidos no mapa de enquadramento da UC.
   - Espaçamento vertical de segurança (8 mm) evitando sobreposição com o título inferior.
4. Rótulos das Feições:
   - Supressão de identificadores internos de banco de dados (52663_hist, etc.).
   - Denominação limpa e padronizada: "Alerta DETER".
5. Ocupação e Proporção da Legenda:
   - Moldura redimensionada proporcionalmente para 18 mm de altura, eliminando áreas vazias.
   - Redistribuição harmônica do espaço para a caixa de fontes (29.2 mm).
"""

import os
import json
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.patheffects as patheffects
import geopandas as gpd
from shapely.geometry import box, Point
from PIL import Image
import contextily as cx

class QGISLayoutEngine:
    def __init__(self, layout_json_path=None):
        self.width_mm = 297.0
        self.height_mm = 210.0
        self.layout_spec = {}
        if layout_json_path and os.path.exists(layout_json_path):
            with open(layout_json_path, "r", encoding="utf-8") as f:
                self.layout_spec = json.load(f)
                if "pages" in self.layout_spec and len(self.layout_spec["pages"]) > 0:
                    self.width_mm = self.layout_spec["pages"][0].get("width_mm", 297.0)
                    self.height_mm = self.layout_spec["pages"][0].get("height_mm", 210.0)

        self.fig = None
        self.ax_canvas = None

    def _mm_to_norm(self, x_mm, y_mm, w_mm, h_mm):
        """Converte milímetros do QGIS (origem topo-esquerda) para normativo Matplotlib (origem base-esquerda)."""
        x_norm = x_mm / self.width_mm
        y_norm = (self.height_mm - (y_mm + h_mm)) / self.height_mm
        w_norm = w_mm / self.width_mm
        h_norm = h_mm / self.height_mm
        return [x_norm, y_norm, w_norm, h_norm]

    def create_layout(self):
        """Inicializa a prancha A4 Paisagem exata."""
        fig_w_in = self.width_mm / 25.4
        fig_h_in = self.height_mm / 25.4
        self.fig = plt.figure(figsize=(fig_w_in, fig_h_in), dpi=300)
        self.fig.patch.set_facecolor("#FFFFFF")

        self.ax_canvas = self.fig.add_axes([0, 0, 1, 1])
        self.ax_canvas.axis("off")
        self.ax_canvas.set_xlim(0, self.width_mm)
        self.ax_canvas.set_ylim(0, self.height_mm)

    def draw_frames(self):
        """Desenha todas as molduras geométricas com proporção equilibrada e sem sobreposições."""
        # Moldura externa da prancha
        self.ax_canvas.add_patch(
            patches.Rectangle((2.5, 2.5), self.width_mm - 5.0, self.height_mm - 5.0,
                              linewidth=1.2, edgecolor="#2C3E50", facecolor="none", zorder=1)
        )

        # Caixa do Título Principal
        self.ax_canvas.add_patch(
            patches.Rectangle((8.0, self.height_mm - (5.411 + 12.302)), 281.0, 12.302,
                              linewidth=1.0, edgecolor="#2C3E50", facecolor="#F8F9F9", zorder=2)
        )

        # Painel Direito de Enquadramento
        self.ax_canvas.add_patch(
            patches.Rectangle((175.254, self.height_mm - (19.0 + 179.5)), 113.746, 179.5,
                              linewidth=1.0, edgecolor="#2C3E50", facecolor="#FAFAFA", zorder=2)
        )

        # Caixa da Legenda (Redimensionada proporcionalmente para 18.0 mm de altura)
        self.ax_canvas.add_patch(
            patches.Rectangle((8.0, self.height_mm - (151.251 + 18.0)), 108.697, 18.0,
                              linewidth=0.8, edgecolor="#2C3E50", facecolor="#FFFFFF", zorder=2)
        )

        # Caixa de Fonte e Metadados Geodésicos (Expandida verticalmente para 29.259 mm)
        self.ax_canvas.add_patch(
            patches.Rectangle((8.0, self.height_mm - (169.251 + 29.259)), 108.697, 29.259,
                              linewidth=0.8, edgecolor="#2C3E50", facecolor="#F8F9F9", zorder=2)
        )

        # Caixa da Escala, Seta Norte e Logotipos
        self.ax_canvas.add_patch(
            patches.Rectangle((116.697, self.height_mm - (151.251 + 47.259)), 58.557, 47.259,
                              linewidth=0.8, edgecolor="#2C3E50", facecolor="#FFFFFF", zorder=2)
        )

    def draw_header_and_titles(self, titulo_mapa, subtitulo_unidade="PARQUE ESTADUAL CHARAPUCU"):
        """Insere o título principal e os cabeçalhos dos painéis de localização."""
        y_titulo = self.height_mm - 5.411 - 6.2
        self.ax_canvas.text(
            148.5, y_titulo,
            titulo_mapa,
            ha="center", va="center",
            fontfamily="sans-serif", fontweight="bold", fontsize=10.5, color="#1B2631", zorder=5
        )

        # Título do Inset Superior (Localização da Ocorrência na UC)
        self.ax_canvas.text(
            232.127, self.height_mm - 21.0,
            "LOCALIZAÇÃO DA OCORRÊNCIA NA UC",
            ha="center", va="center",
            fontfamily="sans-serif", fontweight="bold", fontsize=8.2, color="#1B2631", zorder=5
        )

        # Título do Inset Inferior (Localização da Unidade no Pará)
        # Posicionado com recuo seguro (y=105.0) para nunca colidir com as coordenadas do mapa superior
        self.ax_canvas.text(
            232.127, self.height_mm - 105.0,
            f"LOCALIZAÇÃO DA UNIDADE – {subtitulo_unidade.upper()}",
            ha="center", va="center",
            fontfamily="sans-serif", fontweight="bold", fontsize=8.2, color="#1B2631", zorder=5
        )

    def draw_metadata_and_sources(self, autor="Núcleo de Geotecnologias (NGEO / IDEFLOR-Bio)"):
        """
        Escreve o bloco de notas de rodapé com controle rígido de largura e margem inferior,
        sem colidir com os logos institucionais à direita nem com a moldura inferior.
        """
        x = 10.0
        # Inicia com 3.5 mm de margem do topo da caixa (y_topo = 169.251)
        y_top = self.height_mm - 169.251 - 3.8
        linhas = [
            f"Elaboração: {autor}",
            "Sistema de Coordenadas: Geográficas | Datum: SIRGAS 2000 (EPSG:4674)",
            "Insumo Óptico: Mosaico Sentinel-2 MSI / Copernicus (Cloudless 2025, Resolução 10m, EOX)",
            "Bases Vetoriais: Alertas DETER/INPE (TerraBrasilis, 2019); Limites DGMUC/IDEFLOR-Bio; IBGE",
            "Nota: Mapeamento oficial de suporte técnico ao diagnóstico de restauração e fiscalização."
        ]
        texto = "\n".join(linhas)
        self.ax_canvas.text(
            x, y_top, texto,
            ha="left", va="top",
            fontfamily="sans-serif", fontsize=5.3, color="#2C3E50", linespacing=1.45, zorder=5
        )

    def draw_north_arrow(self):
        """Desenha a rosa dos ventos centralizada no eixo de simetria do bloco técnico (x_center = 145.976 mm)."""
        x_center = 116.697 + 58.557 / 2
        w_mm = 11.0
        h_mm = 12.0
        x_left = x_center - (w_mm / 2)
        y_top = 153.2

        ax_norte = self.fig.add_axes(self._mm_to_norm(x_left, y_top, w_mm, h_mm))
        ax_norte.axis("off")
        ax_norte.set_xlim(0, 1)
        ax_norte.set_ylim(0, 1)

        ax_norte.fill([0.5, 0.5, 0.2, 0.5], [0.12, 0.82, 0.35, 0.12], color="#2C3E50")
        ax_norte.fill([0.5, 0.5, 0.8, 0.5], [0.12, 0.82, 0.35, 0.12], color="#FFFFFF", edgecolor="#2C3E50", linewidth=0.8)
        ax_norte.text(0.5, 0.95, "N", ha="center", va="center", fontsize=8.5, fontweight="bold", color="#1B2631")

    def draw_scale_bar(self, length_km, scale_text="1 : 35.000"):
        """Desenha a escala gráfica métrica centralizada no mesmo eixo da seta norte."""
        x_center = 116.697 + 58.557 / 2
        w_mm = 30.0
        h_mm = 9.5
        x_left = x_center - (w_mm / 2)
        y_top = 168.0

        ax_escala = self.fig.add_axes(self._mm_to_norm(x_left, y_top, w_mm, h_mm))
        ax_escala.axis("off")
        ax_escala.set_xlim(0, 1)
        ax_escala.set_ylim(0, 1)

        ax_escala.fill([0.1, 0.5, 0.5, 0.1], [0.52, 0.52, 0.68, 0.68], color="#2C3E50")
        ax_escala.fill([0.5, 0.9, 0.9, 0.5], [0.52, 0.52, 0.68, 0.68], color="#FFFFFF", edgecolor="#2C3E50", linewidth=0.6)

        ax_escala.text(0.1, 0.76, "0", ha="center", va="bottom", fontsize=5.5, fontweight="bold", color="#1B2631")
        ax_escala.text(0.5, 0.76, f"{length_km/2:g}", ha="center", va="bottom", fontsize=5.5, fontweight="bold", color="#1B2631")
        ax_escala.text(0.9, 0.76, f"{length_km:g} km", ha="center", va="bottom", fontsize=5.5, fontweight="bold", color="#1B2631")
        ax_escala.text(0.5, 0.28, f"Escala {scale_text}", ha="center", va="top", fontsize=6.2, fontweight="bold", color="#1B2631")

    def draw_logos(self, path_ngeo, path_ideflor, path_gov_pa):
        """Renderiza os logotipos com espaçamento generoso e livre de sobreposições."""
        logos = [
            (path_ngeo, 118.5, 181.5, 12.5, 13.5),
            (path_ideflor, 135.5, 181.5, 17.5, 13.5),
            (path_gov_pa, 157.5, 181.5, 13.0, 13.5)
        ]

        for p, x, y, w, h in logos:
            if p and os.path.exists(p):
                try:
                    img = Image.open(p)
                    ax_logo = self.fig.add_axes(self._mm_to_norm(x, y, w, h))
                    ax_logo.imshow(img)
                    ax_logo.axis("off")
                except Exception as e:
                    print(f"[Aviso] Falha ao renderizar logo {p}: {e}")

    def render_macro_map(self, gdf_estados, gdf_paises, gdf_uc):
        """
        Renderiza o Mapa Macro (Contexto do Estado do Pará e Países Vizinhos).
        Posição: x=183.0, y=110.0, w=98.0, h=72.0.
        """
        ax = self.fig.add_axes(self._mm_to_norm(183.0, 110.0, 98.0, 72.0))
        ax.set_facecolor("#EBF5FB")

        xmin, ymin, xmax, ymax = -61.9, -11.0, -43.5, 3.8
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)

        if gdf_paises is not None:
            paises_proj = gdf_paises.to_crs(epsg=4674)
            paises_proj.plot(ax=ax, facecolor="#E5E7E9", edgecolor="#BDC3C7", linewidth=0.4, zorder=2)

        if gdf_estados is not None:
            estados_proj = gdf_estados.to_crs(epsg=4674)
            vizinhos = estados_proj[estados_proj["SIGLA_UF"] != "PA"]
            pa = estados_proj[estados_proj["SIGLA_UF"] == "PA"]

            vizinhos.plot(ax=ax, facecolor="#F2F4F4", edgecolor="#BDC3C7", linewidth=0.4, zorder=3)
            pa.plot(ax=ax, facecolor="#FEF9E7", edgecolor="#7D6608", linewidth=0.8, zorder=4)

            siglas_pos = {
                "AP": (-51.8, 1.5),
                "MA": (-45.2, -4.5),
                "TO": (-48.2, -8.5),
                "MT": (-54.5, -10.5),
                "AM": (-60.0, -4.0),
                "RR": (-61.0, 2.0),
                "PA": (-53.0, -4.0)
            }
            for uf, pos in siglas_pos.items():
                cor = "#7D6608" if uf == "PA" else "#7F8C8D"
                ax.text(pos[0], pos[1], uf, fontsize=5.8, fontweight="bold", color=cor, ha="center", va="center", zorder=6)

        ax.text(-55.5, 3.1, "SURINAME", fontsize=4.5, color="#7F8C8D", style="italic", ha="center", zorder=6)
        ax.text(-52.5, 3.0, "GUIANA FRANCESA", fontsize=4.5, color="#7F8C8D", style="italic", ha="center", zorder=6)
        ax.text(-47.0, 1.8, "OCEANO\nATLÂNTICO", fontsize=5.0, color="#2980B9", style="italic", fontweight="bold", ha="center", zorder=6)

        if gdf_uc is not None and len(gdf_uc) > 0:
            uc_proj = gdf_uc.to_crs(epsg=4674)
            centroid = uc_proj.union_all().centroid if hasattr(uc_proj, "union_all") else uc_proj.unary_union.centroid

            uc_proj.plot(ax=ax, facecolor="#E74C3C", edgecolor="#922B21", linewidth=0.6, zorder=7)
            ax.plot(centroid.x, centroid.y, marker="o", markersize=7, color="#E74C3C", alpha=0.35, zorder=8)
            ax.plot(centroid.x, centroid.y, marker="o", markersize=3.8, color="#E74C3C", markeredgecolor="#FFFFFF", markeredgewidth=0.6, zorder=9)
            ax.text(centroid.x + 0.6, centroid.y + 0.3, "PES Charapucu", fontsize=5.5, fontweight="bold", color="#900C3F",
                    bbox=dict(boxstyle="square,pad=0.15", facecolor="#FFFFFF", edgecolor="#E74C3C", alpha=0.9), zorder=10)

        for spine in ax.spines.values():
            spine.set_edgecolor("#2C3E50")
            spine.set_linewidth(0.8)

        # Grade e coordenadas sutis no mapa macro
        ax.set_xticks([-58.0, -52.0, -46.0])
        ax.set_yticks([-8.0, -4.0, 0.0])
        ax.set_xticklabels(["58° W", "52° W", "46° W"], fontsize=4.8, color="#1B2631")
        ax.set_yticklabels(["8° S", "4° S", "0°"], fontsize=4.8, color="#1B2631")
        for label in ax.get_yticklabels():
            label.set_rotation(90)
            label.set_verticalalignment("center")
        ax.tick_params(axis="both", which="both", direction="out", length=2.0, width=0.5, pad=1.5)
        ax.grid(color="#BDC3C7", linestyle=":", linewidth=0.4, alpha=0.6)

    def render_intermediate_map(self, gdf_uc, gdf_alvo, gdf_municipios=None):
        """
        Renderiza o Mapa Intermediário (Enquadramento no PES Charapucu).
        - Coordenadas e grade 100% restabelecidas nos eixos X e Y.
        - Posição: x=183.0, y=25.0, w=98.0, h=66.0.
        - As coordenadas inferiores terminam em y=94.5 mm, deixando um buffer livre de 10.5 mm
          até o título do mapa inferior (em y=105.0 mm), eliminando qualquer sobreposição.
        """
        ax = self.fig.add_axes(self._mm_to_norm(183.0, 25.0, 98.0, 66.0))
        ax.set_facecolor("#D4E6F1")

        uc_proj = gdf_uc.to_crs(epsg=4674)
        bounds = uc_proj.total_bounds
        pad_x = (bounds[2] - bounds[0]) * 0.12
        pad_y = (bounds[3] - bounds[1]) * 0.12

        ax.set_xlim(bounds[0] - pad_x, bounds[2] + pad_x)
        ax.set_ylim(bounds[1] - pad_y, bounds[3] + pad_y)

        if gdf_municipios is not None:
            mun_proj = gdf_municipios.to_crs(epsg=4674)
            mun_proj.plot(ax=ax, facecolor="#F8F9F9", edgecolor="#BDC3C7", linewidth=0.4, zorder=2)

        uc_proj.plot(ax=ax, facecolor="#A9DFBF", edgecolor="#196F3D", linewidth=1.2, zorder=3)

        c_uc = uc_proj.union_all().centroid if hasattr(uc_proj, "union_all") else uc_proj.unary_union.centroid
        ax.text(c_uc.x - 0.05, c_uc.y + 0.08, "PES Charapucu",
                fontsize=6.2, fontweight="bold", color="#196F3D", ha="center", va="center", zorder=5)

        if gdf_alvo is not None and len(gdf_alvo) > 0:
            alvo_proj = gdf_alvo.to_crs(epsg=4674)
            alvo_proj.plot(ax=ax, facecolor="#E74C3C", edgecolor="#900C3F", linewidth=1.0, zorder=6)

            c_alvo = alvo_proj.union_all().centroid if hasattr(alvo_proj, "union_all") else alvo_proj.unary_union.centroid
            ax.plot(c_alvo.x, c_alvo.y, marker="o", markersize=7, color="#E74C3C", alpha=0.35, zorder=7)
            ax.plot(c_alvo.x, c_alvo.y, marker="o", markersize=3.8, color="#E74C3C", markeredgecolor="#FFFFFF", markeredgewidth=0.6, zorder=8)

            ax.annotate("Área Auditada\n(DETER)",
                        xy=(c_alvo.x, c_alvo.y), xytext=(c_alvo.x - 0.13, c_alvo.y - 0.08),
                        arrowprops=dict(facecolor="#900C3F", edgecolor="#FFFFFF", width=0.8, headwidth=3.5, shrink=0.08),
                        fontsize=5.5, fontweight="bold", color="#900C3F",
                        bbox=dict(boxstyle="round,pad=0.2", facecolor="#FFFFFF", edgecolor="#E74C3C", alpha=0.9),
                        zorder=10)

        for spine in ax.spines.values():
            spine.set_edgecolor("#2C3E50")
            spine.set_linewidth(0.8)

        # RESTAURAÇÃO DA GRADE E COORDENADAS CARTOGRÁFICAS
        lon_ticks = np.linspace(bounds[0], bounds[2], 3)
        lat_ticks = np.linspace(bounds[1], bounds[3], 3)

        ax.set_xticks(lon_ticks)
        ax.set_yticks(lat_ticks)
        ax.set_xticklabels([f"{abs(lon):.2f}° W" for lon in lon_ticks], fontsize=5.0, color="#1B2631", fontweight="bold")
        ax.set_yticklabels([f"{abs(lat):.2f}° S" for lat in lat_ticks], fontsize=5.0, color="#1B2631", fontweight="bold")

        for label in ax.get_yticklabels():
            label.set_rotation(90)
            label.set_verticalalignment("center")

        ax.tick_params(axis="both", which="both", direction="out", length=2.5, width=0.6, pad=1.5)
        ax.grid(color="#BDC3C7", linestyle=":", linewidth=0.5, alpha=0.7)

    def render_main_map(self, gdf_alvo, eox_year="2025"):
        """
        Renderiza o Mapa Principal:
        - Viewport 100% preenchida pela imagem de satélite, sem faixas pretas ou vazios.
        - A borda da viewport É a moldura do mapa; os ticks e coordenadas ancoram-se exatamente nela.
        - Rótulo interno limpo: 'Alerta DETER' (sem IDs técnicos de banco de dados).
        """
        # Dimensões exatas da janela do mapa de detalhe:
        # x = 11.5 mm, y = 18.5 mm, w = 160.5 mm, h = 128.5 mm
        map_x_mm = 11.5
        map_y_mm = 18.5
        map_w_mm = 160.5
        map_h_mm = 128.5

        ax = self.fig.add_axes(self._mm_to_norm(map_x_mm, map_y_mm, map_w_mm, map_h_mm))

        alvo_3857 = gdf_alvo.to_crs(epsg=3857)
        c = alvo_3857.union_all().centroid if hasattr(alvo_3857, "union_all") else alvo_3857.unary_union.centroid
        b = alvo_3857.total_bounds

        # Proporção física exata da janela (w / h)
        phys_ratio = map_w_mm / map_h_mm

        # Enquadramento calibrado para a área de corte raso com buffer equilibrado (~800 m)
        span_y = (b[3] - b[1]) + 1600.0
        span_x = span_y * phys_ratio

        xmin = c.x - (span_x / 2.0)
        xmax = c.x + (span_x / 2.0)
        ymin = c.y - (span_y / 2.0)
        ymax = c.y + (span_y / 2.0)

        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)

        # 1. Carrega os tiles Sentinel-2 Cloudless EOX
        eox_url = f"https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-{eox_year}_3857/default/GoogleMapsCompatible/{{z}}/{{y}}/{{x}}.jpg"
        try:
            print(f"[INFO] Baixando mosaico EOX Sentinel-2 Cloudless ({eox_year})...")
            cx.add_basemap(ax, source=eox_url, zoom=14, reset_extent=False)
            print("[OK] Basemap EOX integrado com sucesso.")
        except Exception as e:
            print(f"[Aviso] Falha ao baixar EOX, utilizando fallback Esri World Imagery: {e}")
            try:
                cx.add_basemap(ax, source=cx.providers.Esri.WorldImagery, zoom=14, reset_extent=False)
            except Exception as e2:
                print(f"[Aviso] Sem conexão com provedores: {e2}")

        # Re-enforça limites exatos e elimina qualquer letterboxing
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ax.set_aspect("auto")
        ax.margins(0)

        # 2. Polígonos de Corte Raso DETER Oficiais
        alvo_3857.plot(
            ax=ax,
            facecolor="#E74C3C",
            edgecolor="#FFD700",
            linewidth=1.8,
            alpha=0.55,
            zorder=6
        )

        # 3. Rótulos padronizados limpos: "Alerta DETER" (sem IDs internos de base de dados)
        pe_stroke = [patheffects.withStroke(linewidth=3.0, foreground="#000000")]
        for _, row in alvo_3857.iterrows():
            centroid_pt = row.geometry.centroid
            t = ax.text(
                centroid_pt.x, centroid_pt.y, "Alerta DETER",
                ha="center", va="center",
                fontsize=7.5, fontweight="bold", color="#FFFFFF",
                bbox=dict(boxstyle="round,pad=0.28", facecolor="#1B2631", edgecolor="#FFD700", alpha=0.90),
                zorder=10
            )
            t.set_path_effects(pe_stroke)

        # 4. Grade de Coordenadas Geográficas ancorada diretamente nos limites do mapa
        pts_geo_min = gpd.GeoSeries([Point(xmin, ymin)], crs=3857).to_crs(epsg=4674).iloc[0]
        pts_geo_max = gpd.GeoSeries([Point(xmax, ymax)], crs=3857).to_crs(epsg=4674).iloc[0]

        lon_vals = np.linspace(pts_geo_min.x, pts_geo_max.x, 6)[1:-1]
        lat_vals = np.linspace(pts_geo_min.y, pts_geo_max.y, 6)[1:-1]

        x_ticks = [gpd.GeoSeries([Point(lon, (pts_geo_min.y+pts_geo_max.y)/2)], crs=4674).to_crs(epsg=3857).iloc[0].x for lon in lon_vals]
        y_ticks = [gpd.GeoSeries([Point((pts_geo_min.x+pts_geo_max.x)/2, lat)], crs=4674).to_crs(epsg=3857).iloc[0].y for lat in lat_vals]

        ax.set_xticks(x_ticks)
        ax.set_yticks(y_ticks)

        # Rótulos externos ancorados na linha visível do mapa
        ax.set_xticklabels([f"{abs(lon):.3f}° W" for lon in lon_vals], fontsize=6.2, color="#1B2631", fontweight="bold")
        ax.set_yticklabels([f"{abs(lat):.3f}° S" for lat in lat_vals], fontsize=6.2, color="#1B2631", fontweight="bold")

        for label in ax.get_yticklabels():
            label.set_rotation(90)
            label.set_verticalalignment("center")

        # Ticks direcionados para fora da moldura sem invadir outros blocos
        ax.tick_params(axis="both", which="both", direction="out", length=3.0, width=0.8, color="#2C3E50", pad=2.5)

        # Malha suave de coordenadas
        ax.grid(color="#FFFFFF", linestyle=":", linewidth=0.5, alpha=0.45)

        # A moldura do mapa é exatamente o contorno dos eixos
        for spine in ax.spines.values():
            spine.set_edgecolor("#2C3E50")
            spine.set_linewidth(1.0)

        # Escala métrica calculada para a largura física da janela (160.5 mm)
        largura_km = (xmax - xmin) / 1000.0
        escala_km = 1.0 if largura_km < 4.0 else 2.0
        escala_num = int(round((largura_km * 1000) / (map_w_mm / 1000.0), -3))
        self.draw_scale_bar(length_km=escala_km, scale_text=f"1 : {escala_num:,}".replace(",", "."))

    def render_legend(self):
        """
        Desenha a Legenda Cartográfica Normativa:
        - Caixa proporcional e harmoniosa (altura 18.0 mm), preenchendo o espaço sem vazios residuais.
        - Cabeçalho padronizado: 'LEGENDA'.
        - Classe única vetorizada: 'Corte Raso (DETER / INPE)'.
        """
        # Caixa ajustada: x=8.0, y=151.251, w=108.697, h=18.0 mm
        ax_leg = self.fig.add_axes(self._mm_to_norm(9.5, 152.0, 105.0, 16.5))
        ax_leg.axis("off")
        ax_leg.set_xlim(0, 100)
        ax_leg.set_ylim(0, 16)

        ax_leg.text(1, 12.0, "LEGENDA", fontsize=7.6, fontweight="bold", color="#1B2631")

        # Símbolo retangular e denominação temática
        ax_leg.add_patch(
            patches.Rectangle((2, 3.0), 8, 5.5, facecolor="#E74C3C", edgecolor="#FFD700", linewidth=1.2, alpha=0.65)
        )
        ax_leg.text(13, 5.8, "Corte Raso (DETER / INPE)", fontsize=6.8, fontweight="bold", va="center", color="#2C3E50")

    def export(self, output_png_path, output_pdf_path=None, dpi=300):
        """Salva a prancha cartográfica em PNG de alta resolução e PDF vetorial."""
        os.makedirs(os.path.dirname(output_png_path), exist_ok=True)
        print(f"[INFO] Exportando prancha cartográfica em {dpi} DPI...")
        self.fig.savefig(output_png_path, dpi=dpi, facecolor=self.fig.get_facecolor(), bbox_inches="tight")
        print(f"[OK] Imagem PNG salva: {output_png_path}")

        if output_pdf_path:
            os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
            self.fig.savefig(output_pdf_path, dpi=dpi, facecolor=self.fig.get_facecolor(), bbox_inches="tight")
            print(f"[OK] PDF vetorial salvo: {output_pdf_path}")
        plt.close(self.fig)
