"""
Motor Cartográfico QGIS para Python / Colab (qgis_layout_engine.py)
Reproduz com fidelidade milimétrica o layout A4 Paisagem (297 x 210 mm)
extraído do QGIS (NGEO/IDEFLOR-Bio).

Hierarquia Cartográfica dos 3 Mapas:
1. Mapa Macro (Localização da Unidade): Pará no contexto dos estados e países vizinhos.
2. Mapa Intermediário (Localização da Ocorrência): A área dentro do PES Charapucu.
3. Mapa Principal: Zoom de detalhe nas glebas com imagem de satélite Sentinel-2 EOX.
"""

import os
import json
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.patheffects as patheffects
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
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

        # Configurações de DPI e figura
        self.fig = None
        self.axes = {}

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

        # Fundo base para desenho de molduras gerais
        self.ax_canvas = self.fig.add_axes([0, 0, 1, 1])
        self.ax_canvas.axis("off")
        self.ax_canvas.set_xlim(0, self.width_mm)
        self.ax_canvas.set_ylim(0, self.height_mm)

    def draw_frames(self):
        """Desenha todas as molduras geométricas e caixas de fundo extraídas do QGIS."""
        # Moldura externa da prancha
        self.ax_canvas.add_patch(
            patches.Rectangle((2, 2), self.width_mm - 4, self.height_mm - 4,
                              linewidth=1.2, edgecolor="#2C3E50", facecolor="none", zorder=1)
        )

        # Caixa do Título
        self.ax_canvas.add_patch(
            patches.Rectangle((8.0, self.height_mm - (5.411 + 12.302)), 278.85, 12.302,
                              linewidth=1.0, edgecolor="#2C3E50", facecolor="#F8F9F9", zorder=2)
        )

        # Moldura do Mapa Geral
        self.ax_canvas.add_patch(
            patches.Rectangle((8.15, self.height_mm - (14.108 + 137.143)), 167.106, 137.143,
                              linewidth=1.0, edgecolor="#2C3E50", facecolor="#FFFFFF", zorder=2)
        )

        # Moldura do Painel de Localização (Direita)
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

    def draw_header_and_titles(self, titulo_mapa, subtitulo_unidade="PARQUE ESTADUAL CHARAPUCU"):
        """Insere os títulos oficiais e cabeçalhos cartográficos."""
        y_titulo = self.height_mm - 5.411 - 6.5
        self.ax_canvas.text(
            147.4, y_titulo,
            titulo_mapa,
            ha="center", va="center",
            fontfamily="sans-serif", fontweight="bold", fontsize=11, color="#1B2631", zorder=5
        )

        # Título do Inset Superior (Localização da Ocorrência)
        y_txt_ocorrencia = self.height_mm - 14.108 - 4.5
        self.ax_canvas.text(
            175.256 + 111.462 / 2, y_txt_ocorrencia,
            "LOCALIZAÇÃO DA OCORRÊNCIA NA UC",
            ha="center", va="center",
            fontfamily="sans-serif", fontweight="bold", fontsize=8.5, color="#1B2631", zorder=5
        )

        # Título do Inset Inferior (Localização da Unidade)
        y_txt_unidade = self.height_mm - 103.319 - 4.5
        self.ax_canvas.text(
            175.388 + 111.462 / 2, y_txt_unidade,
            f"LOCALIZAÇÃO DA UNIDADE – {subtitulo_unidade.upper()}",
            ha="center", va="center",
            fontfamily="sans-serif", fontweight="bold", fontsize=8.5, color="#1B2631", zorder=5
        )

    def draw_metadata_and_sources(self, autor="Núcleo de Geotecnologias (NGEO/IDEFLOR-Bio)",
                                  fontes="INPE / DETER (TerraBrasilis); IDEFLOR-Bio; EOX Sentinel-2 Cloudless (2025)"):
        """Escreve a nota de fontes cartográficas, datum e autoria."""
        x = 9.5
        y_top = self.height_mm - 184.135 - 3.2
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
            fontfamily="sans-serif", fontsize=5.8, color="#2C3E50", linespacing=1.3, zorder=5
        )

    def draw_logos(self, path_ngeo, path_ideflor, path_gov_pa):
        """Renderiza os logotipos institucionais nos boxes exatos."""
        # Posições em mm
        logos = [
            (path_ngeo, 122.76, 181.528, 13.238, 15.279),
            (path_ideflor, 137.5, 181.528, 17.806, 15.0),
            (path_gov_pa, 157.066, 181.072, 15.024, 15.087)
        ]

        for p, x, y, w, h in logos:
            if p and os.path.exists(p):
                try:
                    img = Image.open(p)
                    # Cria um axes minúsculo para cada logo
                    ax_logo = self.fig.add_axes(self._mm_to_norm(x, y, w, h))
                    ax_logo.imshow(img)
                    ax_logo.axis("off")
                except Exception as e:
                    print(f"[Aviso] Falha ao renderizar logo {p}: {e}")

    def draw_north_arrow(self):
        """Desenha rosa dos ventos / seta norte cartográfica."""
        # Caixa de seta norte: x=141.844, y=153.554, w=11.162, h=13.435
        ax_norte = self.fig.add_axes(self._mm_to_norm(142.0, 153.0, 11.0, 13.5))
        ax_norte.axis("off")
        ax_norte.set_xlim(0, 1)
        ax_norte.set_ylim(0, 1)

        # Desenha a seta norte elegante estilo poligonal bipartido (preto/branco)
        ax_norte.fill([0.5, 0.5, 0.2, 0.5], [0.1, 0.85, 0.35, 0.1], color="#2C3E50")
        ax_norte.fill([0.5, 0.5, 0.8, 0.5], [0.1, 0.85, 0.35, 0.1], color="#FFFFFF", edgecolor="#2C3E50", linewidth=0.8)
        ax_norte.text(0.5, 0.95, "N", ha="center", va="center", fontsize=9, fontweight="bold", color="#1B2631")

    def draw_scale_bar(self, length_km, scale_text="1 : 35.000"):
        """Desenha a barra de escala gráfica métrica e texto de escala numérica."""
        # Caixa: x=119.097, y=167.0, w=22.0, h=11.0
        ax_escala = self.fig.add_axes(self._mm_to_norm(118.5, 166.5, 23.0, 11.0))
        ax_escala.axis("off")
        ax_escala.set_xlim(0, 1)
        ax_escala.set_ylim(0, 1)

        # Barra bipartida
        ax_escala.fill([0.05, 0.45, 0.45, 0.05], [0.45, 0.45, 0.60, 0.60], color="#2C3E50")
        ax_escala.fill([0.45, 0.85, 0.85, 0.45], [0.45, 0.45, 0.60, 0.60], color="#FFFFFF", edgecolor="#2C3E50", linewidth=0.6)

        # Rótulos
        ax_escala.text(0.05, 0.70, "0", ha="center", va="bottom", fontsize=5.5, fontweight="bold")
        ax_escala.text(0.45, 0.70, f"{length_km/2:g}", ha="center", va="bottom", fontsize=5.5, fontweight="bold")
        ax_escala.text(0.85, 0.70, f"{length_km:g} km", ha="center", va="bottom", fontsize=5.5, fontweight="bold")
        ax_escala.text(0.45, 0.25, f"Escala {scale_text}", ha="center", va="top", fontsize=6.2, fontweight="bold", color="#1B2631")

    def render_macro_map(self, gdf_estados, gdf_paises, gdf_uc):
        """
        Renderiza o Mapa Macro (Localização da Unidade no Estado do Pará).
        Posição exata do QGIS: x=181.698, y=112.245, w=98.579, h=80.0
        """
        ax = self.fig.add_axes(self._mm_to_norm(181.698, 112.245, 98.579, 80.0))
        ax.set_facecolor("#EBF5FB") # Oceano / Água clara

        # Extensão oficial do Pará com vizinhos
        xmin, ymin, xmax, ymax = -61.9, -11.0, -43.5, 3.8
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)

        # 1. Países da América do Sul (vizinhos continentais)
        if gdf_paises is not None:
            paises_proj = gdf_paises.to_crs(epsg=4674)
            paises_proj.plot(ax=ax, facecolor="#F2F4F4", edgecolor="#BDC3C7", linewidth=0.4, zorder=2)

        # 2. Estados Brasileiros vizinhos
        if gdf_estados is not None:
            estados_proj = gdf_estados.to_crs(epsg=4674)
            vizinhos = estados_proj[estados_proj["SIGLA_UF"] != "PA"]
            pa = estados_proj[estados_proj["SIGLA_UF"] == "PA"]

            vizinhos.plot(ax=ax, facecolor="#EAEDED", edgecolor="#BDC3C7", linewidth=0.5, zorder=3)
            pa.plot(ax=ax, facecolor="#D5F5E3", edgecolor="#1E8449", linewidth=0.9, zorder=4)

            # Rótulos dos Estados
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
                peso = "bold"
                ax.text(pos[0], pos[1], uf, fontsize=6.5, fontweight=peso, color=cor, ha="center", va="center", zorder=6)

        # 3. Rótulos de Países / Oceano
        ax.text(-55.5, 3.2, "SURINAME", fontsize=5, color="#7F8C8D", style="italic", ha="center", zorder=6)
        ax.text(-52.5, 3.0, "GUIANA FRANCESA", fontsize=5, color="#7F8C8D", style="italic", ha="center", zorder=6)
        ax.text(-47.0, 1.8, "OCEANO\nATLÂNTICO", fontsize=5.5, color="#2980B9", style="italic", fontweight="bold", ha="center", zorder=6)

        # 4. Unidade de Conservação (PES Charapucu)
        if gdf_uc is not None and len(gdf_uc) > 0:
            uc_proj = gdf_uc.to_crs(epsg=4674)
            # Como a UC tem ~0.35 graus e o estado tem 15 graus, plota a geometria E um marcador de destaque
            uc_proj.plot(ax=ax, facecolor="#E74C3C", edgecolor="#922B21", linewidth=0.8, zorder=7)

            centroid = uc_proj.unary_union.centroid
            # Halo circular
            ax.plot(centroid.x, centroid.y, marker="o", markersize=9, color="#E74C3C", alpha=0.3, zorder=8)
            ax.plot(centroid.x, centroid.y, marker="o", markersize=5, color="#E74C3C", markeredgecolor="#FFFFFF", markeredgewidth=0.8, zorder=9)
            # Chamada de texto
            ax.text(centroid.x + 0.6, centroid.y + 0.3, "PES Charapucu", fontsize=6, fontweight="bold", color="#900C3F",
                    bbox=dict(boxstyle="square,pad=0.15", facecolor="#FFFFFF", edgecolor="#E74C3C", alpha=0.9), zorder=10)

        # Grade cartográfica discreta
        ax.tick_params(axis="both", which="both", labelsize=5, length=2, color="#7F8C8D")
        ax.grid(color="#BDC3C7", linestyle=":", linewidth=0.4, alpha=0.7)
        ax.set_title("CONTEXTO ESTADUAL (PARÁ)", fontsize=7, fontweight="bold", pad=2, color="#1B2631")

    def render_intermediate_map(self, gdf_uc, gdf_alvo, gdf_municipios=None):
        """
        Renderiza o Mapa Intermediário (Localização da Ocorrência no PES Charapucu).
        Posição exata do QGIS: x=181.83, y=23.169, w=98.579, h=80.0
        """
        ax = self.fig.add_axes(self._mm_to_norm(181.83, 23.169, 98.579, 80.0))
        ax.set_facecolor("#EBF5FB") # Água / Rios estuarinos de Afuá

        uc_proj = gdf_uc.to_crs(epsg=4674)
        bounds = uc_proj.total_bounds # [xmin, ymin, xmax, ymax]
        pad_x = (bounds[2] - bounds[0]) * 0.15
        pad_y = (bounds[3] - bounds[1]) * 0.15

        xmin, ymin = bounds[0] - pad_x, bounds[1] - pad_y
        xmax, ymax = bounds[2] + pad_x, bounds[3] + pad_y
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)

        # Município de Afuá no entorno se disponível
        if gdf_municipios is not None:
            mun_proj = gdf_municipios.to_crs(epsg=4674)
            mun_proj.plot(ax=ax, facecolor="#F4F6F7", edgecolor="#BDC3C7", linewidth=0.5, zorder=2)

        # Parque Estadual Charapucu
        uc_proj.plot(ax=ax, facecolor="#D4EFDF", edgecolor="#1E8449", linewidth=1.2, zorder=3)

        # Rótulo da UC
        c_uc = uc_proj.unary_union.centroid
        ax.text(c_uc.x - 0.05, c_uc.y + 0.08, "PES Charapucu\n(72.506 ha)",
                fontsize=6.2, fontweight="bold", color="#196F3D", ha="center", va="center", zorder=5)

        # Rótulo de água circundante (Baía de Vieira Grande / Rio Vieira Grande)
        ax.text(bounds[2] + 0.02, (bounds[1] + bounds[3])/2, "Baía de\nVieira Grande",
                fontsize=5.5, color="#2980B9", style="italic", ha="left", va="center", zorder=5)

        # Alvo (Ocorrência DETER)
        if gdf_alvo is not None and len(gdf_alvo) > 0:
            alvo_proj = gdf_alvo.to_crs(epsg=4674)
            # Polígono do alvo destacado
            alvo_proj.plot(ax=ax, facecolor="#E74C3C", edgecolor="#900C3F", linewidth=1.0, zorder=6)

            # Ponto de chamada / halo para visualização imediata
            c_alvo = alvo_proj.unary_union.centroid
            ax.plot(c_alvo.x, c_alvo.y, marker="o", markersize=8, color="#E74C3C", alpha=0.35, zorder=7)
            ax.plot(c_alvo.x, c_alvo.y, marker="o", markersize=4.5, color="#E74C3C", markeredgecolor="#FFFFFF", markeredgewidth=0.8, zorder=8)

            # Texto apontando para a área
            ax.annotate("Área Auditada\n(183,76 ha)",
                        xy=(c_alvo.x, c_alvo.y), xytext=(c_alvo.x - 0.12, c_alvo.y - 0.08),
                        arrowprops=dict(facecolor="#900C3F", edgecolor="#FFFFFF", width=0.8, headwidth=4, shrink=0.08),
                        fontsize=5.8, fontweight="bold", color="#900C3F",
                        bbox=dict(boxstyle="round,pad=0.2", facecolor="#FFFFFF", edgecolor="#E74C3C", alpha=0.9),
                        zorder=10)

        ax.tick_params(axis="both", which="both", labelsize=5, length=2, color="#7F8C8D")
        ax.grid(color="#BDC3C7", linestyle=":", linewidth=0.4, alpha=0.7)
        ax.set_title("ENQUADRAMENTO NO PARQUE ESTADUAL", fontsize=7, fontweight="bold", pad=2, color="#1B2631")

    def render_main_map(self, gdf_alvo, gdf_uc=None, eox_year="2025", buffer_meters=1200):
        """
        Renderiza o Mapa Principal (Zoom de Detalhe nas Glebas DETER com Satélite EOX).
        Posição exata do QGIS: x=11.762, y=17.68, w=160.0, h=130.0
        """
        ax = self.fig.add_axes(self._mm_to_norm(11.762, 17.68, 160.0, 130.0))

        # Projeção Web Mercator (EPSG:3857) ideal para tiles de satélite de alta definição
        alvo_3857 = gdf_alvo.to_crs(epsg=3857)
        b = alvo_3857.total_bounds # [xmin, ymin, xmax, ymax] em metros

        # Buffer harmonioso para manter escala ~1:30.000 ou 1:35.000
        xmin = b[0] - buffer_meters
        ymin = b[1] - buffer_meters
        xmax = b[2] + buffer_meters
        ymax = b[3] + buffer_meters

        # Ajusta para o aspect ratio de 160 / 130 = 1.2307
        target_ratio = 160.0 / 130.0
        curr_w = xmax - xmin
        curr_h = ymax - ymin
        curr_ratio = curr_w / curr_h

        if curr_ratio < target_ratio:
            diff = (curr_h * target_ratio) - curr_w
            xmin -= diff / 2
            xmax += diff / 2
        else:
            diff = (curr_w / target_ratio) - curr_h
            ymin -= diff / 2
            ymax += diff / 2

        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)

        # 1. Carrega o Basemap Sentinel-2 Cloudless EOX
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
                print(f"[Aviso] Sem conexão com provedores de imagem: {e2}")
                ax.set_facecolor("#2E4053")

        # 2. Limite do Parque Estadual Charapucu (se passar no enquadramento)
        if gdf_uc is not None:
            uc_3857 = gdf_uc.to_crs(epsg=3857)
            uc_clip = gpd.clip(uc_3857, box(xmin, ymin, xmax, ymax))
            if not uc_clip.empty:
                uc_clip.boundary.plot(ax=ax, color="#2ECC71", linestyle="--", linewidth=1.8, zorder=5)

        # 3. Alertas DETER Oficiais
        # Contorno com brilho externo (path effects) para alto contraste sobre o satélite
        pe_stroke = [patheffects.withStroke(linewidth=3.5, foreground="#000000")]

        alvo_3857.plot(
            ax=ax,
            facecolor="#E74C3C",
            edgecolor="#FFD700", # Borda amarela ouro brilhante
            linewidth=1.8,
            alpha=0.45,
            zorder=6
        )

        # 4. Rótulos informativos de cada talhão com área em ha
        for _, row in alvo_3857.iterrows():
            c = row.geometry.centroid
            gid = row.get("alerta_id", row.get("gid", "Alerta"))
            area = row.get("area_ha", 0.0)
            txt = f"Alerta {gid}\nÁrea: {area:.2f} ha\nClasse: Corte Raso (DETER)"

            t = ax.text(
                c.x, c.y, txt,
                ha="center", va="center",
                fontsize=7.2, fontweight="bold", color="#FFFFFF",
                bbox=dict(boxstyle="round,pad=0.25", facecolor="#1B2631", edgecolor="#FFD700", alpha=0.85),
                zorder=10
            )
            t.set_path_effects(pe_stroke)

        # 5. Coordenadas nas bordas (convertidas para SIRGAS 2000 em graus decimais nos ticks)
        ax.tick_params(axis="both", which="both", labelsize=6.5, length=3, color="#1B2631")
        # Formatador customizado para exibir lat/lon em graus decimais nas bordas
        # Transformando ticks de 3857 para 4674:
        xticks = ax.get_xticks()
        yticks = ax.get_yticks()

        pts_x = gpd.GeoSeries([Point(x, (ymin+ymax)/2) for x in xticks], crs=3857).to_crs(epsg=4674)
        pts_y = gpd.GeoSeries([Point((xmin+xmax)/2, y) for y in yticks], crs=3857).to_crs(epsg=4674)

        ax.set_xticks(xticks)
        ax.set_xticklabels([f"{p.x:.3f}°W" for p in pts_x])
        ax.set_yticks(yticks)
        ax.set_yticklabels([f"{p.y:.3f}°S" for p in pts_y])

        ax.grid(color="#FFFFFF", linestyle="--", linewidth=0.5, alpha=0.4)

        # Calcula a largura do mapa em km para desenhar a escala gráfica
        largura_km = (xmax - xmin) / 1000.0
        # Normaliza escala bonita (ex: 1 km ou 2 km)
        escala_km = 1.0 if largura_km < 4.0 else 2.0
        # Escala aproximada na folha (160mm)
        escala_num = int(round((largura_km * 1000) / 0.160, -3))
        self.draw_scale_bar(length_km=escala_km, scale_text=f"1 : {escala_num:,}".replace(",", "."))

    def render_legend(self):
        """Desenha a legenda cartográfica com as simbologias das camadas."""
        # Caixa: x=8.15, y=151.251, w=108.543, h=32.883
        ax_leg = self.fig.add_axes(self._mm_to_norm(9.5, 152.0, 105.0, 31.0))
        ax_leg.axis("off")
        ax_leg.set_xlim(0, 100)
        ax_leg.set_ylim(0, 30)

        # Título da legenda
        ax_leg.text(1, 26, "LEGENDA CONVENCIONADA", fontsize=7.5, fontweight="bold", color="#1B2631")

        # Itens da Legenda
        itens = [
            ("Área de Corte Raso Auditada (DETER/INPE - 183,76 ha)", "#E74C3C", "#FFD700", "polygon"),
            ("Limite do Parque Estadual Charapucu (72.506 ha)", "#2ECC71", "#2ECC71", "line_dash"),
            ("Corpos Hídricos & Várzea Estuarina (Baía Vieira Grande)", "#EBF5FB", "#2980B9", "polygon"),
            ("Mosaico Sentinel-2 Cloudless EOX (Resolução 10m)", "#2C3E50", "#2C3E50", "raster")
        ]

        y_pos = 20
        for label, fcolor, ecolor, stype in itens:
            if stype == "polygon":
                ax_leg.add_patch(patches.Rectangle((2, y_pos - 1.5), 6, 4, facecolor=fcolor, edgecolor=ecolor, linewidth=1.0, alpha=0.7))
            elif stype == "line_dash":
                ax_leg.plot([2, 8], [y_pos + 0.5, y_pos + 0.5], color=ecolor, linestyle="--", linewidth=1.5)
            elif stype == "raster":
                ax_leg.add_patch(patches.Rectangle((2, y_pos - 1.5), 6, 4, facecolor="#5D6D7E", edgecolor="#2C3E50", linewidth=0.8))

            ax_leg.text(11, y_pos, label, fontsize=6.2, va="center", color="#2C3E50")
            y_pos -= 6.2

    def export(self, output_png_path, output_pdf_path=None, dpi=300):
        """Salva a prancha cartográfica em PNG e/ou PDF."""
        os.makedirs(os.path.dirname(output_png_path), exist_ok=True)
        print(f"[INFO] Exportando prancha cartográfica em {dpi} DPI...")
        self.fig.savefig(output_png_path, dpi=dpi, facecolor=self.fig.get_facecolor(), bbox_inches="tight")
        print(f"[OK] Mapa exportado com sucesso: {output_png_path}")

        if output_pdf_path:
            os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
            self.fig.savefig(output_pdf_path, dpi=dpi, facecolor=self.fig.get_facecolor(), bbox_inches="tight")
            print(f"[OK] PDF vetorial exportado com sucesso: {output_pdf_path}")
        plt.close(self.fig)
