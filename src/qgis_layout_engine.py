"""
Motor Cartográfico QGIS para Python / Colab (qgis_layout_engine.py)
Reproduz com fidelidade milimétrica e elegância o layout A4 Paisagem (297 x 210 mm)
extraído do QGIS (NGEO/IDEFLOR-Bio).

Refinamentos de Precisão Cartográfica:
1. Snap da grade a valores redondos/cheios (ex: 0.01° no principal, 0.10° no intermediário, 5° no macro).
2. Supressão de rótulos dos cantos para evitar qualquer colisão X/Y ou transbordamento da moldura.
3. Rótulos minimalistas nas feições: feição grande com texto e halo/buffer sutil; feição pequena com rótulo deslocado e seta apontando, sem cobrir a geometria.
4. Dimensões rigorosamente idênticas para os dois mapas de apoio (98.0 x 70.0 mm), garantindo harmonia visual.
5. Todos os eixos Y com coordenadas em sentido vertical ascendente (90°).
6. Títulos diretos e limpos (sem subtítulos desnecessários).
7. Seta norte e barra de escala centralizadas horizontalmente.
8. Legenda contemplando todas as camadas temáticas ativas na prancha.
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
        """Desenha todas as molduras geométricas originais da prancha."""
        # Moldura externa da prancha
        self.ax_canvas.add_patch(
            patches.Rectangle((2.0, 2.0), self.width_mm - 4.0, self.height_mm - 4.0,
                              linewidth=1.2, edgecolor="#2C3E50", facecolor="none", zorder=1)
        )

        # Caixa do Título Principal
        self.ax_canvas.add_patch(
            patches.Rectangle((8.0, self.height_mm - (5.411 + 12.302)), 278.85, 12.302,
                              linewidth=1.0, edgecolor="#2C3E50", facecolor="#F8F9F9", zorder=2)
        )

        # Moldura Externa do Mapa Geral
        self.ax_canvas.add_patch(
            patches.Rectangle((8.15, self.height_mm - (14.108 + 137.143)), 167.106, 137.143,
                              linewidth=1.0, edgecolor="#2C3E50", facecolor="#FFFFFF", zorder=2)
        )

        # Painel Direito de Enquadramento
        self.ax_canvas.add_patch(
            patches.Rectangle((175.254, self.height_mm - (14.108 + 184.402)), 111.466, 184.402,
                              linewidth=1.0, edgecolor="#2C3E50", facecolor="#FAFAFA", zorder=2)
        )

        # Caixa da Legenda
        self.ax_canvas.add_patch(
            patches.Rectangle((8.15, self.height_mm - (151.251 + 32.883)), 108.543, 32.883,
                              linewidth=0.8, edgecolor="#2C3E50", facecolor="#FFFFFF", zorder=2)
        )

        # Caixa de Fonte e Informações Geodésicas
        self.ax_canvas.add_patch(
            patches.Rectangle((8.15, self.height_mm - (184.135 + 14.375)), 108.543, 14.375,
                              linewidth=0.8, edgecolor="#2C3E50", facecolor="#F8F9F9", zorder=2)
        )

        # Caixa da Escala, Seta Norte e Logos
        self.ax_canvas.add_patch(
            patches.Rectangle((116.697, self.height_mm - (151.251 + 47.259)), 58.559, 47.259,
                              linewidth=0.8, edgecolor="#2C3E50", facecolor="#FFFFFF", zorder=2)
        )

    def draw_header_and_titles(self, titulo_mapa):
        """Insere o título principal e os títulos simples e diretos dos mapas de apoio."""
        y_titulo = self.height_mm - 5.411 - 6.5
        self.ax_canvas.text(
            147.4, y_titulo,
            titulo_mapa,
            ha="center", va="center",
            fontfamily="sans-serif", fontweight="bold", fontsize=10.5, color="#1B2631", zorder=5
        )

        # Título simples do Inset Superior (sem subtítulo)
        self.ax_canvas.text(
            230.987, self.height_mm - 18.0,
            "LOCALIZAÇÃO DA OCORRÊNCIA NA UC",
            ha="center", va="center",
            fontfamily="sans-serif", fontweight="bold", fontsize=8.2, color="#1B2631", zorder=5
        )

        # Título simples do Inset Inferior (posicionado com espaço seguro em y = 105.0 mm)
        self.ax_canvas.text(
            230.987, self.height_mm - 105.0,
            "LOCALIZAÇÃO DA UNIDADE – PARQUE ESTADUAL CHARAPUCU",
            ha="center", va="center",
            fontfamily="sans-serif", fontweight="bold", fontsize=8.0, color="#1B2631", zorder=5
        )

    def draw_metadata_and_sources(self, autor="Núcleo de Geotecnologias (NGEO/IDEFLOR-Bio)",
                                  fontes="INPE / DETER (TerraBrasilis); IDEFLOR-Bio; EOX Sentinel-2 Cloudless (2025)"):
        """Escreve a nota de fontes cartográficas, datum e insumo de satélite."""
        x = 9.8
        y_top = self.height_mm - 184.135 - 3.0
        linhas = [
            f"Elaboração: {autor}",
            "Sistema Geodésico de Referência: SIRGAS 2000 (EPSG:4674 / UTM Fuso 22N)",
            f"Fontes de Dados: {fontes}",
            "Nota: Mapeamento oficial de suporte à gestão e fiscalização ambiental."
        ]
        texto = "\n".join(linhas)
        self.ax_canvas.text(
            x, y_top, texto,
            ha="left", va="top",
            fontfamily="sans-serif", fontsize=5.8, color="#2C3E50", linespacing=1.35, zorder=5
        )

    def draw_north_arrow(self):
        """Desenha a seta norte centralizada horizontalmente no bloco técnico (x_center = 145.976 mm)."""
        x_center = 116.697 + 58.559 / 2
        w_mm = 11.0
        h_mm = 13.0
        x_left = x_center - (w_mm / 2)
        y_top = 153.2

        ax_norte = self.fig.add_axes(self._mm_to_norm(x_left, y_top, w_mm, h_mm))
        ax_norte.axis("off")
        ax_norte.set_xlim(0, 1)
        ax_norte.set_ylim(0, 1)

        ax_norte.fill([0.5, 0.5, 0.2, 0.5], [0.1, 0.85, 0.35, 0.1], color="#2C3E50")
        ax_norte.fill([0.5, 0.5, 0.8, 0.5], [0.1, 0.85, 0.35, 0.1], color="#FFFFFF", edgecolor="#2C3E50", linewidth=0.8)
        ax_norte.text(0.5, 0.96, "N", ha="center", va="center", fontsize=8.5, fontweight="bold", color="#1B2631")

    def draw_scale_bar(self, length_km, scale_text="1 : 36.000"):
        """Desenha a barra de escala gráfica centralizada horizontalmente no mesmo eixo da seta norte."""
        x_center = 116.697 + 58.559 / 2
        w_mm = 32.0
        h_mm = 10.0
        x_left = x_center - (w_mm / 2)
        y_top = 168.0

        ax_escala = self.fig.add_axes(self._mm_to_norm(x_left, y_top, w_mm, h_mm))
        ax_escala.axis("off")
        ax_escala.set_xlim(0, 1)
        ax_escala.set_ylim(0, 1)

        # Barra bipartida
        ax_escala.fill([0.05, 0.45, 0.45, 0.05], [0.45, 0.45, 0.60, 0.60], color="#2C3E50")
        ax_escala.fill([0.45, 0.85, 0.85, 0.45], [0.45, 0.45, 0.60, 0.60], color="#FFFFFF", edgecolor="#2C3E50", linewidth=0.6)

        # Rótulos métricos
        ax_escala.text(0.05, 0.70, "0", ha="center", va="bottom", fontsize=5.5, fontweight="bold")
        ax_escala.text(0.45, 0.70, f"{length_km/2:g}", ha="center", va="bottom", fontsize=5.5, fontweight="bold")
        ax_escala.text(0.85, 0.70, f"{length_km:g} km", ha="center", va="bottom", fontsize=5.5, fontweight="bold")
        ax_escala.text(0.45, 0.22, f"Escala {scale_text}", ha="center", va="top", fontsize=6.2, fontweight="bold", color="#1B2631")

    def draw_logos(self, path_ngeo, path_ideflor, path_gov_pa):
        """Renderiza os 3 logotipos no rodapé da caixa técnica com espaçamento equilibrado."""
        logos = [
            (path_ngeo, 121.5, 181.5, 12.5, 14.5),
            (path_ideflor, 137.0, 181.5, 17.5, 14.5),
            (path_gov_pa, 158.0, 181.5, 13.5, 14.5)
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
        Renderiza o Mapa Macro (Pará no contexto dos estados e países vizinhos).
        Dimensões rigorosamente idênticas ao mapa intermediário: w = 98.0 mm, h = 70.0 mm.
        Posição: x = 182.0, y = 110.5 mm.
        Snap da grade em valores redondos (5°), rótulos dos cantos suprimidos e eixo Y a 90°.
        """
        w_mm = 98.0
        h_mm = 70.0
        ax = self.fig.add_axes(self._mm_to_norm(182.0, 110.5, w_mm, h_mm))
        ax.set_facecolor("#EBF5FB")

        xmin, ymin, xmax, ymax = -61.9, -11.0, -43.5, 3.8
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)

        if gdf_paises is not None:
            paises_proj = gdf_paises.to_crs(epsg=4674)
            paises_proj.plot(ax=ax, facecolor="#F2F4F4", edgecolor="#BDC3C7", linewidth=0.4, zorder=2)

        if gdf_estados is not None:
            estados_proj = gdf_estados.to_crs(epsg=4674)
            vizinhos = estados_proj[estados_proj["SIGLA_UF"] != "PA"]
            pa = estados_proj[estados_proj["SIGLA_UF"] == "PA"]

            vizinhos.plot(ax=ax, facecolor="#EAEDED", edgecolor="#BDC3C7", linewidth=0.5, zorder=3)
            pa.plot(ax=ax, facecolor="#D5F5E3", edgecolor="#1E8449", linewidth=0.9, zorder=4)

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
                cor = "#196F3D" if uf == "PA" else "#7F8C8D"
                ax.text(pos[0], pos[1], uf, fontsize=6.2, fontweight="bold", color=cor, ha="center", va="center", zorder=6)

        ax.text(-55.5, 3.0, "SURINAME", fontsize=4.8, color="#7F8C8D", style="italic", ha="center", zorder=6)
        ax.text(-52.5, 2.8, "GUIANA FRANCESA", fontsize=4.8, color="#7F8C8D", style="italic", ha="center", zorder=6)
        ax.text(-47.0, 1.8, "OCEANO\nATLÂNTICO", fontsize=5.2, color="#2980B9", style="italic", fontweight="bold", ha="center", zorder=6)

        if gdf_uc is not None and len(gdf_uc) > 0:
            uc_proj = gdf_uc.to_crs(epsg=4674)
            centroid = uc_proj.union_all().centroid if hasattr(uc_proj, "union_all") else uc_proj.unary_union.centroid

            uc_proj.plot(ax=ax, facecolor="#E74C3C", edgecolor="#922B21", linewidth=0.8, zorder=7)
            ax.plot(centroid.x, centroid.y, marker="o", markersize=7, color="#E74C3C", alpha=0.35, zorder=8)
            ax.plot(centroid.x, centroid.y, marker="o", markersize=4.0, color="#E74C3C", markeredgecolor="#FFFFFF", markeredgewidth=0.7, zorder=9)
            ax.text(centroid.x + 0.6, centroid.y + 0.3, "PES Charapucu", fontsize=5.5, fontweight="bold", color="#900C3F",
                    bbox=dict(boxstyle="square,pad=0.15", facecolor="#FFFFFF", edgecolor="#E74C3C", alpha=0.9), zorder=10)

        # Snap da grade em valores redondos (5° e 2°)
        lon_ticks = [-60.0, -55.0, -50.0, -45.0]
        lat_ticks = [-10.0, -8.0, -6.0, -4.0, -2.0, 0.0, 2.0]

        ax.set_xticks(lon_ticks)
        ax.set_yticks(lat_ticks)

        # Suprime os rótulos de canto para não colidir
        ax.set_xticklabels([f"{lon:.0f}°" if i not in [0, len(lon_ticks)-1] else "" for i, lon in enumerate(lon_ticks)], fontsize=5.0)
        ax.set_yticklabels([f"{lat:.0f}°" if i not in [0, len(lat_ticks)-1] else "" for i, lat in enumerate(lat_ticks)], fontsize=5.0)

        for label in ax.get_yticklabels():
            label.set_rotation(90)
            label.set_verticalalignment("center")

        ax.tick_params(axis="both", which="both", labelsize=5.0, length=2.0, color="#7F8C8D", pad=1.5)
        ax.grid(color="#BDC3C7", linestyle=":", linewidth=0.4, alpha=0.7)

    def render_intermediate_map(self, gdf_uc, gdf_alvo, gdf_municipios=None):
        """
        Renderiza o Mapa Intermediário (Enquadramento no PES Charapucu).
        Dimensões rigorosamente idênticas ao mapa macro: w = 98.0 mm, h = 70.0 mm.
        Posição: x = 182.0, y = 23.0 mm.
        Snap da grade em valores redondos (0.10°), cantos suprimidos e eixo Y a 90°.
        """
        w_mm = 98.0
        h_mm = 70.0
        ax = self.fig.add_axes(self._mm_to_norm(182.0, 23.0, w_mm, h_mm))
        ax.set_facecolor("#EBF5FB")

        uc_proj = gdf_uc.to_crs(epsg=4674)
        bounds = uc_proj.total_bounds
        pad_x = (bounds[2] - bounds[0]) * 0.15
        pad_y = (bounds[3] - bounds[1]) * 0.15

        ax.set_xlim(bounds[0] - pad_x, bounds[2] + pad_x)
        ax.set_ylim(bounds[1] - pad_y, bounds[3] + pad_y)

        if gdf_municipios is not None:
            mun_proj = gdf_municipios.to_crs(epsg=4674)
            mun_proj.plot(ax=ax, facecolor="#F4F6F7", edgecolor="#BDC3C7", linewidth=0.5, zorder=2)

        uc_proj.plot(ax=ax, facecolor="#D4EFDF", edgecolor="#1E8449", linewidth=1.2, zorder=3)

        c_uc = uc_proj.union_all().centroid if hasattr(uc_proj, "union_all") else uc_proj.unary_union.centroid
        ax.text(c_uc.x - 0.05, c_uc.y + 0.08, "PES Charapucu",
                fontsize=6.2, fontweight="bold", color="#196F3D", ha="center", va="center", zorder=5)

        ax.text(bounds[2] + 0.02, (bounds[1] + bounds[3])/2, "Baía de\nVieira Grande",
                fontsize=5.2, color="#2980B9", style="italic", ha="left", va="center", zorder=5)

        if gdf_alvo is not None and len(gdf_alvo) > 0:
            alvo_proj = gdf_alvo.to_crs(epsg=4674)
            alvo_proj.plot(ax=ax, facecolor="#E74C3C", edgecolor="#900C3F", linewidth=1.0, zorder=6)

            c_alvo = alvo_proj.union_all().centroid if hasattr(alvo_proj, "union_all") else alvo_proj.unary_union.centroid
            ax.plot(c_alvo.x, c_alvo.y, marker="o", markersize=7, color="#E74C3C", alpha=0.35, zorder=7)
            ax.plot(c_alvo.x, c_alvo.y, marker="o", markersize=3.8, color="#E74C3C", markeredgecolor="#FFFFFF", markeredgewidth=0.7, zorder=8)

            ax.annotate("Área Auditada\n(183,76 ha)",
                        xy=(c_alvo.x, c_alvo.y), xytext=(c_alvo.x - 0.12, c_alvo.y - 0.08),
                        arrowprops=dict(facecolor="#900C3F", edgecolor="#FFFFFF", width=0.8, headwidth=4, shrink=0.08),
                        fontsize=5.5, fontweight="bold", color="#900C3F",
                        bbox=dict(boxstyle="round,pad=0.2", facecolor="#FFFFFF", edgecolor="#E74C3C", alpha=0.9),
                        zorder=10)

        # Snap da grade a valores redondos de 0.10° (ex: -50.60°, -50.50°, -50.40°, -50.30°)
        lon_ticks = np.array([-50.60, -50.50, -50.40, -50.30])
        lat_ticks = np.array([-0.45, -0.35, -0.25])

        ax.set_xticks(lon_ticks)
        ax.set_yticks(lat_ticks)

        # Suprime os rótulos de canto para não tocar na borda
        ax.set_xticklabels([f"{lon:.2f}" if i not in [0, len(lon_ticks)-1] else "" for i, lon in enumerate(lon_ticks)], fontsize=5.0)
        ax.set_yticklabels([f"{lat:.2f}" for lat in lat_ticks], fontsize=5.0)

        # ROTAÇÃO VERTICAL ASCENDENTE NO EIXO Y (90°)
        for label in ax.get_yticklabels():
            label.set_rotation(90)
            label.set_verticalalignment("center")

        ax.tick_params(axis="both", which="both", labelsize=5.0, length=2.0, color="#7F8C8D", pad=1.5)
        ax.grid(color="#BDC3C7", linestyle=":", linewidth=0.4, alpha=0.7)

    def render_main_map(self, gdf_alvo, gdf_uc=None, eox_year="2025"):
        """
        Renderiza o Mapa Principal:
        - Viewport perfeitamente proporcional ao retângulo externo com margem homogênea.
        - Imagem de satélite preenche 100% da área da grade (zero margem interna).
        - Snap da grade a valores redondos (passo de 0.010°).
        - Rótulos dos cantos suprimidos (evita sobreposição X/Y e transbordamento).
        - Rótulos das feições minimalistas:
          * Feição grande (173.28 ha): texto com halo/buffer sutil.
          * Feição pequena (10.48 ha): rótulo deslocado com seta indicativa, sem cobrir o polígono.
        """
        # Dimensões perfeitamente proporcionais ao retângulo externo rec_mapa (167.106 x 137.143):
        # Margem uniforme de 6.0 mm nas laterais e 5.0 mm no topo e fundo:
        map_x_mm = 14.15
        map_y_mm = 18.0
        map_w_mm = 155.0
        map_h_mm = 127.2

        ax = self.fig.add_axes(self._mm_to_norm(map_x_mm, map_y_mm, map_w_mm, map_h_mm))

        alvo_3857 = gdf_alvo.to_crs(epsg=3857)
        c = alvo_3857.union_all().centroid if hasattr(alvo_3857, "union_all") else alvo_3857.unary_union.centroid
        b = alvo_3857.total_bounds

        phys_ratio = map_w_mm / map_h_mm

        span_y = (b[3] - b[1]) + 2000.0
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

        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ax.set_aspect("auto")
        ax.margins(0)

        # 2. Limite REAL da UC se interceptar a viewport
        if gdf_uc is not None and len(gdf_uc) > 0:
            map_box = box(xmin, ymin, xmax, ymax)
            uc_3857 = gdf_uc.to_crs(epsg=3857)
            uc_boundary = uc_3857.geometry.boundary.iloc[0]
            if uc_boundary.intersects(map_box):
                real_boundary_segment = uc_boundary.intersection(map_box)
                gpd.GeoSeries([real_boundary_segment], crs=3857).plot(
                    ax=ax, color="#2ECC71", linestyle="--", linewidth=1.8, zorder=5
                )

        # 3. Polígonos de Corte Raso DETER Oficiais
        alvo_3857.plot(
            ax=ax,
            facecolor="#E74C3C",
            edgecolor="#FFD700",
            linewidth=1.8,
            alpha=0.55,
            zorder=6
        )

        # 4. Rótulos das Feições (Minimalistas e com Tratamento Diferenciado de Escala)
        pe_stroke = [patheffects.withStroke(linewidth=3.0, foreground="#000000")]

        for _, row in alvo_3857.iterrows():
            centroid_pt = row.geometry.centroid
            area_val = row.get("area_ha", 0.0)

            # Diferenciação: feição pequena (< 20 ha) recebe rótulo deslocado com seta para não cobrir o polígono
            if area_val < 20.0:
                ax.annotate(
                    f"Alerta DETER ({area_val:.2f} ha)",
                    xy=(centroid_pt.x, centroid_pt.y),
                    xytext=(centroid_pt.x + 350.0, centroid_pt.y + 350.0),
                    arrowprops=dict(facecolor="#FFD700", edgecolor="#000000", width=1.0, headwidth=4.0, shrink=0.08),
                    fontsize=6.8, fontweight="bold", color="#FFFFFF",
                    bbox=dict(boxstyle="round,pad=0.25", facecolor="#1B2631", edgecolor="#FFD700", alpha=0.88),
                    zorder=10
                ).set_path_effects(pe_stroke)
            else:
                # Feição grande: rótulo minimalista centralizado com halo protetor
                t = ax.text(
                    centroid_pt.x, centroid_pt.y,
                    f"Alerta DETER\n({area_val:.2f} ha)",
                    ha="center", va="center",
                    fontsize=7.2, fontweight="bold", color="#FFFFFF",
                    bbox=dict(boxstyle="round,pad=0.25", facecolor="#1B2631", edgecolor="#FFD700", alpha=0.88),
                    zorder=10
                )
                t.set_path_effects(pe_stroke)

        # 5. Grade de Coordenadas: Snap a Valores Redondos e Supressão dos Cantos
        pts_geo_min = gpd.GeoSeries([Point(xmin, ymin)], crs=3857).to_crs(epsg=4674).iloc[0]
        pts_geo_max = gpd.GeoSeries([Point(xmax, ymax)], crs=3857).to_crs(epsg=4674).iloc[0]

        # Snap a passo de 0.010° (graus redondos e limpos)
        step = 0.010
        start_lon = np.ceil(pts_geo_min.x / step) * step
        end_lon = np.floor(pts_geo_max.x / step) * step
        lon_vals = np.arange(start_lon, end_lon + step/2.0, step)

        start_lat = np.ceil(pts_geo_min.y / step) * step
        end_lat = np.floor(pts_geo_max.y / step) * step
        lat_vals = np.arange(start_lat, end_lat + step/2.0, step)

        x_ticks = [gpd.GeoSeries([Point(lon, (pts_geo_min.y+pts_geo_max.y)/2)], crs=4674).to_crs(epsg=3857).iloc[0].x for lon in lon_vals]
        y_ticks = [gpd.GeoSeries([Point((pts_geo_min.x+pts_geo_max.x)/2, lat)], crs=4674).to_crs(epsg=3857).iloc[0].y for lat in lat_vals]

        ax.set_xticks(x_ticks)
        ax.set_yticks(y_ticks)

        # Rótulos nas bordas externas com supressão dos cantos
        # (O primeiro e último rótulo muito próximos do canto são suprimidos para evitar colisão X/Y)
        x_labels = []
        for i, lon in enumerate(lon_vals):
            # Suprime se for o primeiro ou o último caso estejam muito perto dos limites
            if i == 0 and abs(lon - pts_geo_min.x) < 0.003:
                x_labels.append("")
            elif i == len(lon_vals) - 1 and abs(pts_geo_max.x - lon) < 0.003:
                x_labels.append("")
            else:
                x_labels.append(f"{abs(lon):.2f}°W")

        y_labels = []
        for i, lat in enumerate(lat_vals):
            if i == 0 and abs(lat - pts_geo_min.y) < 0.003:
                y_labels.append("")
            elif i == len(lat_vals) - 1 and abs(pts_geo_max.y - lat) < 0.003:
                y_labels.append("")
            else:
                y_labels.append(f"{abs(lat):.2f}°S")

        ax.set_xticklabels(x_labels, fontsize=6.2, color="#1B2631")
        ax.set_yticklabels(y_labels, fontsize=6.2, color="#1B2631")

        # ROTAÇÃO VERTICAL ASCENDENTE NO EIXO Y (90°)
        for label in ax.get_yticklabels():
            label.set_rotation(90)
            label.set_verticalalignment("center")

        ax.tick_params(axis="both", which="both", direction="out", length=3.0, width=0.8, color="#2C3E50", pad=2.0)
        ax.grid(color="#FFFFFF", linestyle="--", linewidth=0.5, alpha=0.4)

        for spine in ax.spines.values():
            spine.set_edgecolor("#2C3E50")
            spine.set_linewidth(1.0)

        # Escala métrica calculada
        largura_km = (xmax - xmin) / 1000.0
        escala_km = 1.0 if largura_km < 4.0 else 2.0
        escala_num = int(round((largura_km * 1000) / (map_w_mm / 1000.0), -3))
        self.draw_scale_bar(length_km=escala_km, scale_text=f"1 : {escala_num:,}".replace(",", "."))

    def render_legend(self):
        """
        Desenha a Legenda Cartográfica Completa:
        - Inclui estritamente as camadas vetoriais ativas na prancha:
          1. Área de Corte Raso Auditada (DETER/INPE - 183,76 ha)
          2. Limite do Parque Estadual Charapucu
          3. Limite do Estado do Pará (Contexto Regional)
        """
        # Caixa: x=8.15, y=151.251, w=108.543, h=32.883
        ax_leg = self.fig.add_axes(self._mm_to_norm(9.5, 152.0, 105.0, 31.0))
        ax_leg.axis("off")
        ax_leg.set_xlim(0, 100)
        ax_leg.set_ylim(0, 30)

        ax_leg.text(1, 25.0, "LEGENDA CONVENCIONADA", fontsize=7.5, fontweight="bold", color="#1B2631")

        itens = [
            ("Área de Corte Raso Auditada (DETER/INPE - 183,76 ha)", "#E74C3C", "#FFD700", "polygon"),
            ("Limite do Parque Estadual Charapucu", "#1E8449", "#1E8449", "line_dash"),
            ("Limite do Estado do Pará (Contexto Regional)", "#D5F5E3", "#1E8449", "polygon")
        ]

        y_pos = 18.5
        for label, fcolor, ecolor, stype in itens:
            if stype == "polygon":
                ax_leg.add_patch(patches.Rectangle((2, y_pos - 1.5), 6, 4, facecolor=fcolor, edgecolor=ecolor, linewidth=1.0, alpha=0.75))
            elif stype == "line_dash":
                ax_leg.plot([2, 8], [y_pos + 0.5, y_pos + 0.5], color=ecolor, linestyle="--", linewidth=1.5)

            ax_leg.text(11, y_pos, label, fontsize=6.4, va="center", color="#2C3E50")
            y_pos -= 6.8

    def export(self, output_png_path, output_pdf_path=None, dpi=300):
        """Salva a prancha cartográfica em PNG e/ou PDF."""
        os.makedirs(os.path.dirname(output_png_path), exist_ok=True)
        print(f"[INFO] Exportando prancha cartográfica em {dpi} DPI...")
        self.fig.savefig(output_png_path, dpi=dpi, facecolor=self.fig.get_facecolor(), bbox_inches="tight")
        print(f"[OK] Imagem PNG salva: {output_png_path}")

        if output_pdf_path:
            os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
            self.fig.savefig(output_pdf_path, dpi=dpi, facecolor=self.fig.get_facecolor(), bbox_inches="tight")
            print(f"[OK] PDF vetorial salvo: {output_pdf_path}")
        plt.close(self.fig)
