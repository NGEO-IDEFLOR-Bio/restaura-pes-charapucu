"""
Módulo: 04_dashboard_components.py
Descrição: Construtores reutilizáveis de componentes para o Mini-Dashboard Interativo
           do PES Charapucu (Google Colab / Jupyter).
           - Cards de KPI em HTML/CSS responsivo
           - Gráficos analíticos Plotly
           - Mapa temático interativo Folium
"""

import json
from pathlib import Path
import geopandas as gpd
import pandas as pd
import folium
from folium import GeoJson, GeoJsonTooltip, GeoJsonPopup
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Paleta Institucional e Metodológica
CORES_METODOS = {
    "RNA": "#2ecc71",           # Verde Esmeralda
    "Enriquecimento": "#f39c12", # Âmbar / Laranja
    "Plantio Direto": "#e74c3c"  # Carmim / Vermelho
}

CORES_PORTE = {
    "Pequeno (< 5 ha)": "#3498db",
    "Médio (5 - 20 ha)": "#9b59b6",
    "Grande (20 - 50 ha)": "#e67e22",
    "Macro-gleba (> 50 ha)": "#1abc9c"
}


def gerar_cards_kpi(gdf_filtrado: gpd.GeoDataFrame, meta_ha: float = 130.0) -> str:
    """
    Gera bloco HTML com 4 cards de KPIs estilizados e responsivos.
    """
    total_ha = float(gdf_filtrado["area_ha"].sum()) if not gdf_filtrado.empty else 0.0
    total_talhoes = len(gdf_filtrado)
    dist_media = float(gdf_filtrado["dist_margem_m"].mean()) if not gdf_filtrado.empty else 0.0
    
    if not gdf_filtrado.empty and "metodo" in gdf_filtrado.columns:
        metodo_dom = gdf_filtrado.groupby("metodo")["area_ha"].sum().idxmax()
        area_metodo_dom = gdf_filtrado.groupby("metodo")["area_ha"].sum().max()
        perc_metodo_dom = (area_metodo_dom / total_ha) * 100.0 if total_ha > 0 else 0
    else:
        metodo_dom = "Nenhum"
        perc_metodo_dom = 0.0

    perc_meta = (total_ha / meta_ha) * 100.0 if meta_ha > 0 else 0.0
    cor_meta = "#27ae60" if perc_meta >= 100 else "#e67e22"

    html = f"""
    <div style="display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
        <!-- Card 1: Área Total -->
        <div style="flex: 1; min-width: 210px; background: #ffffff; border: 1px solid #e1e8ed; border-left: 5px solid {cor_meta}; border-radius: 8px; padding: 14px 18px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
            <div style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: #7f8c8d; letter-spacing: 0.5px;">Área Total Filtrada</div>
            <div style="font-size: 26px; font-weight: 800; color: #2c3e50; margin: 4px 0;">{total_ha:,.2f} <span style="font-size: 14px; font-weight: 600; color: #7f8c8d;">ha</span></div>
            <div style="font-size: 12px; font-weight: 600; color: {cor_meta};">
                ● {perc_meta:.1f}% da meta básica ({meta_ha:.0f} ha)
            </div>
        </div>

        <!-- Card 2: Contagem de Talhões -->
        <div style="flex: 1; min-width: 210px; background: #ffffff; border: 1px solid #e1e8ed; border-left: 5px solid #2980b9; border-radius: 8px; padding: 14px 18px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
            <div style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: #7f8c8d; letter-spacing: 0.5px;">Glebas Selecionadas</div>
            <div style="font-size: 26px; font-weight: 800; color: #2c3e50; margin: 4px 0;">{total_talhoes} <span style="font-size: 14px; font-weight: 600; color: #7f8c8d;">polígonos</span></div>
            <div style="font-size: 12px; color: #7f8c8d;">
                Média de {(total_ha/total_talhoes if total_talhoes > 0 else 0):.2f} ha/gleba
            </div>
        </div>

        <!-- Card 3: Acesso Fluvial Médio -->
        <div style="flex: 1; min-width: 210px; background: #ffffff; border: 1px solid #e1e8ed; border-left: 5px solid #16a085; border-radius: 8px; padding: 14px 18px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
            <div style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: #7f8c8d; letter-spacing: 0.5px;">Distância aos Furos</div>
            <div style="font-size: 26px; font-weight: 800; color: #2c3e50; margin: 4px 0;">{dist_media:,.1f} <span style="font-size: 14px; font-weight: 600; color: #7f8c8d;">m</span></div>
            <div style="font-size: 12px; color: #7f8c8d;">
                Média até calha navegável
            </div>
        </div>

        <!-- Card 4: Método Predominante -->
        <div style="flex: 1; min-width: 210px; background: #ffffff; border: 1px solid #e1e8ed; border-left: 5px solid #8e44ad; border-radius: 8px; padding: 14px 18px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
            <div style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: #7f8c8d; letter-spacing: 0.5px;">Método Predominante</div>
            <div style="font-size: 22px; font-weight: 800; color: #2c3e50; margin: 4px 0;">{metodo_dom}</div>
            <div style="font-size: 12px; color: #7f8c8d;">
                Representa {perc_metodo_dom:.1f}% da área filtrada
            </div>
        </div>
    </div>
    """
    return html


def gerar_graficos_analiticos(gdf_filtrado: gpd.GeoDataFrame) -> go.Figure:
    """
    Gera painel interativo Plotly com 2 gráficos lado a lado:
    1. Donut Chart: Distribuição de Área por Método de Restauração
    2. Bar Chart: Área Total e Quantidade por Classe de Porte
    """
    if gdf_filtrado.empty:
        fig = go.Figure()
        fig.add_annotation(text="Nenhum dado selecionado nos filtros.", showarrow=False, font=dict(size=16))
        fig.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
        return fig

    # Criar subplots: 1 linha, 2 colunas
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "domain"}, {"type": "xy"}]],
        subplot_titles=[
            "<b>Proporção da Área por Método</b>",
            "<b>Distribuição por Classe de Porte</b>"
        ]
    )

    # 1. Gráfico de Donut por Método
    df_metodo = gdf_filtrado.groupby("metodo")["area_ha"].sum().reset_index()
    cores_deste_grafico = [CORES_METODOS.get(m, "#95a5a6") for m in df_metodo["metodo"]]

    fig.add_trace(
        go.Pie(
            labels=df_metodo["metodo"],
            values=df_metodo["area_ha"],
            hole=0.55,
            marker=dict(colors=cores_deste_grafico, line=dict(color="#ffffff", width=2)),
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>Área: %{value:.2f} ha<br>Participação: %{percent}<extra></extra>"
        ),
        row=1, col=1
    )

    # 2. Gráfico de Barras por Classe de Porte
    ordem_portes = ["Pequeno (< 5 ha)", "Médio (5 - 20 ha)", "Grande (20 - 50 ha)", "Macro-gleba (> 50 ha)"]
    df_porte = gdf_filtrado.groupby("classe_area").agg(
        area_total=("area_ha", "sum"),
        qtd=("id_gleba", "count")
    ).reindex(ordem_portes).dropna(how="all").reset_index()

    cores_porte = [CORES_PORTE.get(p, "#34495e") for p in df_porte["classe_area"]]

    fig.add_trace(
        go.Bar(
            x=df_porte["classe_area"],
            y=df_porte["area_total"],
            marker=dict(color=cores_porte, line=dict(color="#ffffff", width=1)),
            text=[f"{v:.1f} ha<br>({q} un)" for v, q in zip(df_porte["area_total"], df_porte["qtd"])],
            textposition="auto",
            hovertemplate="<b>%{x}</b><br>Área: %{y:.2f} ha<extra></extra>"
        ),
        row=1, col=2
    )

    fig.update_layout(
        height=360,
        margin=dict(l=20, r=20, t=50, b=20),
        showlegend=False,
        plot_bgcolor="#fdfdfd",
        paper_bgcolor="#ffffff",
        font=dict(family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif", size=12)
    )
    fig.update_yaxes(title_text="Área (ha)", row=1, col=2, gridcolor="#edf2f7")
    fig.update_xaxes(row=1, col=2)

    return fig


def construir_mapa_reativo(
    gdf_filtrado: gpd.GeoDataFrame,
    gdf_parque_geo: gpd.GeoDataFrame = None
) -> folium.Map:
    """
    Constrói mapa interativo Folium com tiles de Satélite e vetores temáticos.
    """
    # Centro aproximado do PES Charapucu
    centro_lat, centro_lon = -0.3414, -50.4998

    m = folium.Map(
        location=[centro_lat, centro_lon],
        zoom_start=11,
        tiles=None,
        control_scale=True
    )

    # Basemaps: Esri Satellite e CartoDB Positron
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satélite (Esri)",
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles="CartoDB positron",
        name="CartoDB Positron (Claro)",
        overlay=False,
        control=True
    ).add_to(m)

    # Camada do Limite Oficial do Parque
    if gdf_parque_geo is not None and not gdf_parque_geo.empty:
        folium.GeoJson(
            gdf_parque_geo,
            name="Limite Oficial PES Charapucu",
            style_function=lambda x: {
                "color": "#00ffff",
                "weight": 2.5,
                "fillColor": "#000000",
                "fillOpacity": 0.0,
                "dashArray": "4, 4"
            },
            tooltip="<b>Parque Estadual Charapucu</b><br>Área: 72.506 ha"
        ).add_to(m)

    # Camada dos Talhões Filtrados
    if not gdf_filtrado.empty:
        # Garantir WGS 84
        gdf_wgs84 = gdf_filtrado.to_crs("EPSG:4326").copy()

        def estilo_talhao(feature):
            metodo = feature["properties"].get("metodo", "Enriquecimento")
            cor = CORES_METODOS.get(metodo, "#f39c12")
            return {
                "color": cor,
                "weight": 1.5,
                "fillColor": cor,
                "fillOpacity": 0.65
            }

        geojson_layer = GeoJson(
            gdf_wgs84,
            name="Talhões Elegíveis à Restauração",
            style_function=estilo_talhao,
            tooltip=GeoJsonTooltip(
                fields=["id_gleba", "metodo", "area_ha", "dist_margem_m", "acesso_fluvial"],
                aliases=["Gleba:", "Método:", "Área (ha):", "Dist. Furo (m):", "Acesso:"],
                localize=True
            ),
            popup=GeoJsonPopup(
                fields=["id_gleba", "metodo", "area_ha", "classe_area", "acesso_fluvial", "dist_margem_m", "setor_fluvial", "centroide_lat", "centroide_lon"],
                aliases=["ID:", "Método:", "Área (ha):", "Porte:", "Acesso:", "Distância:", "Setor:", "Latitude:", "Longitude:"],
                localize=True,
                labels=True
            )
        )
        geojson_layer.add_to(m)

    folium.LayerControl(position="topright", collapsed=False).add_to(m)
    return m
