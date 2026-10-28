"""
Módulo: 04_dashboard_components.py
Descrição: Construtores modulares de componentes para o Mini-Dashboard Interativo
           do PES Charapucu (Google Colab / Jupyter).
           - Foco: DIAGNÓSTICO GEOESPACIAL DE COBERTURA E SEVERIDADE (para apoio à decisão da Gestão)
           - Cards de KPI em HTML/CSS responsivo
           - Gráficos analíticos Plotly
           - Mapa temático interativo Folium com basemaps livres e legenda flutuante
"""

import json
from pathlib import Path
import geopandas as gpd
import pandas as pd
import folium
from folium import GeoJson, GeoJsonTooltip, GeoJsonPopup
from branca.element import Element
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Paleta Visual por Classe de Diagnóstico
CORES_DIAGNOSTICO = {
    "Clareira Aberta / Baixa Biomassa": "#e74c3c",  # Vermelho (Severidade Alta)
    "Dossel Ralo / Alteração Moderada": "#f39c12",  # Âmbar / Laranja (Moderada)
    "Regeneração em Curso": "#2ecc71"              # Verde Esmeralda (Dinâmica Natural)
}

CORES_PORTE = {
    "Pequeno (< 5 ha)": "#3498db",
    "Médio (5 - 20 ha)": "#9b59b6",
    "Grande (20 - 50 ha)": "#e67e22",
    "Macro-gleba (> 50 ha)": "#1abc9c"
}


def gerar_cards_kpi(gdf_filtrado: gpd.GeoDataFrame, meta_ha: float = 130.0) -> str:
    """
    Gera bloco HTML com 4 cards de KPIs estilizados e responsivos para diagnóstico.
    """
    total_ha = float(gdf_filtrado["area_ha"].sum()) if not gdf_filtrado.empty else 0.0
    total_talhoes = len(gdf_filtrado)
    dist_media = float(gdf_filtrado["dist_margem_m"].mean()) if not gdf_filtrado.empty else 0.0
    
    col_diag = "diagnostico" if "diagnostico" in gdf_filtrado.columns else ("metodo" if "metodo" in gdf_filtrado.columns else None)
    if not gdf_filtrado.empty and col_diag:
        diag_dom = gdf_filtrado.groupby(col_diag)["area_ha"].sum().idxmax()
        area_diag_dom = gdf_filtrado.groupby(col_diag)["area_ha"].sum().max()
        perc_diag_dom = (area_diag_dom / total_ha) * 100.0 if total_ha > 0 else 0
    else:
        diag_dom = "Nenhum"
        perc_diag_dom = 0.0

    perc_meta = (total_ha / meta_ha) * 100.0 if meta_ha > 0 else 0.0
    cor_meta = "#27ae60" if perc_meta >= 100 else "#e67e22"

    html = f"""
    <div style="display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
        <!-- Card 1: Área Total Diagnosticada -->
        <div style="flex: 1; min-width: 210px; background: #ffffff; border: 1px solid #e1e8ed; border-left: 5px solid {cor_meta}; border-radius: 8px; padding: 14px 18px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
            <div style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: #7f8c8d; letter-spacing: 0.5px;">Área Diagnosticada</div>
            <div style="font-size: 26px; font-weight: 800; color: #2c3e50; margin: 4px 0;">{total_ha:,.2f} <span style="font-size: 14px; font-weight: 600; color: #7f8c8d;">ha</span></div>
            <div style="font-size: 12px; font-weight: 600; color: {cor_meta};">
                ● {perc_meta:.1f}% da meta referencial ({meta_ha:.0f} ha)
            </div>
        </div>

        <!-- Card 2: Contagem de Polígonos -->
        <div style="flex: 1; min-width: 210px; background: #ffffff; border: 1px solid #e1e8ed; border-left: 5px solid #2980b9; border-radius: 8px; padding: 14px 18px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
            <div style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: #7f8c8d; letter-spacing: 0.5px;">Glebas Diagnosticadas</div>
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

        <!-- Card 4: Diagnóstico Predominante -->
        <div style="flex: 1; min-width: 210px; background: #ffffff; border: 1px solid #e1e8ed; border-left: 5px solid #8e44ad; border-radius: 8px; padding: 14px 18px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
            <div style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: #7f8c8d; letter-spacing: 0.5px;">Diagnóstico Predominante</div>
            <div style="font-size: 19px; font-weight: 800; color: #2c3e50; margin: 4px 0;">{diag_dom}</div>
            <div style="font-size: 12px; color: #7f8c8d;">
                Representa {perc_diag_dom:.1f}% da área filtrada
            </div>
        </div>
    </div>
    """
    return html


def gerar_graficos_analiticos(gdf_filtrado: gpd.GeoDataFrame) -> go.Figure:
    """
    Gera painel interativo Plotly com 2 gráficos lado a lado:
    1. Donut Chart: Distribuição de Área por Diagnóstico de Cobertura
    2. Bar Chart: Área Total e Quantidade por Classe de Porte
    """
    if gdf_filtrado.empty:
        fig = go.Figure()
        fig.add_annotation(text="Nenhum dado selecionado nos filtros.", showarrow=False, font=dict(size=16))
        fig.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
        return fig

    col_diag = "diagnostico" if "diagnostico" in gdf_filtrado.columns else "metodo"

    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "domain"}, {"type": "xy"}]],
        subplot_titles=[
            "<b>Área por Diagnóstico de Cobertura</b>",
            "<b>Distribuição por Classe de Porte</b>"
        ]
    )

    # 1. Gráfico de Donut por Diagnóstico
    df_diag = gdf_filtrado.groupby(col_diag)["area_ha"].sum().reset_index()
    cores_diag = [CORES_DIAGNOSTICO.get(d, "#95a5a6") for d in df_diag[col_diag]]

    fig.add_trace(
        go.Pie(
            labels=df_diag[col_diag],
            values=df_diag["area_ha"],
            hole=0.55,
            marker=dict(colors=cores_diag, line=dict(color="#ffffff", width=2)),
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

    cores_portes = [CORES_PORTE.get(p, "#34495e") for p in df_porte["classe_area"]]

    fig.add_trace(
        go.Bar(
            x=df_porte["classe_area"],
            y=df_porte["area_total"],
            text=[f"{val:.1f} ha<br>({qtd} un)" for val, qtd in zip(df_porte["area_total"], df_porte["qtd"])],
            textposition="auto",
            marker=dict(color=cores_portes, line=dict(color="#2c3e50", width=1)),
            hovertemplate="<b>%{x}</b><br>Área Total: %{y:.2f} ha<extra></extra>"
        ),
        row=1, col=2
    )

    fig.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=50, b=20),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif", size=11, color="#2c3e50"),
        showlegend=False
    )
    fig.update_yaxes(title_text="Área Acumulada (ha)", gridcolor="#edf2f7", row=1, col=2)
    fig.update_xaxes(gridcolor="#edf2f7", row=1, col=2)

    return fig


def construir_mapa_reativo(
    gdf_filtrado: gpd.GeoDataFrame,
    gdf_parque: gpd.GeoDataFrame = None,
    centro_lat: float = -0.3414,
    centro_lon: float = -50.4998
) -> folium.Map:
    """
    Constrói o mapa interativo Folium com basemaps abertos da Esri e Legenda de Diagnóstico.
    """
    m = folium.Map(
        location=[centro_lat, centro_lon],
        zoom_start=11,
        tiles=None,
        control_scale=True
    )

    # Basemaps Esri (100% livres, sem restrição de API Key e sem bloqueio em Colab/Jupyter)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satélite (Esri World Imagery)",
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Light Gray",
        name="Mapa Claro (Esri Light Gray)",
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Topo Map",
        name="Topográfico (Esri Topo)",
        overlay=False,
        control=True
    ).add_to(m)

    # Camada do Limite Oficial do Parque
    if gdf_parque is not None and not gdf_parque.empty:
        gdf_parque_geo = gdf_parque.to_crs("EPSG:4326") if gdf_parque.crs != "EPSG:4326" else gdf_parque
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
        gdf_wgs84 = gdf_filtrado.to_crs("EPSG:4326").copy() if gdf_filtrado.crs != "EPSG:4326" else gdf_filtrado.copy()

        def estilo_talhao(feature):
            d = feature["properties"].get("diagnostico") or feature["properties"].get("metodo", "Dossel Ralo / Alteração Moderada")
            cor = CORES_DIAGNOSTICO.get(d, "#f39c12")
            return {
                "color": cor,
                "weight": 1.5,
                "fillColor": cor,
                "fillOpacity": 0.65
            }

        campos_tooltip = ["id_gleba", "diagnostico", "severidade", "area_ha", "dist_margem_m", "acesso_fluvial"]
        aliases_tooltip = ["Gleba:", "Diagnóstico:", "Severidade:", "Área (ha):", "Dist. Furo (m):", "Acesso:"]
        
        # Ajuste se colunas antigas
        campos_tooltip = [c for c in campos_tooltip if c in gdf_wgs84.columns]
        aliases_tooltip = aliases_tooltip[:len(campos_tooltip)]

        campos_popup = ["id_gleba", "diagnostico", "severidade", "area_ha", "classe_area", "acesso_fluvial", "dist_margem_m", "setor_fluvial"]
        aliases_popup = ["ID:", "Diagnóstico:", "Severidade:", "Área (ha):", "Porte:", "Acesso:", "Distância:", "Setor:"]
        campos_popup = [c for c in campos_popup if c in gdf_wgs84.columns]
        aliases_popup = aliases_popup[:len(campos_popup)]

        geojson_layer = GeoJson(
            gdf_wgs84,
            name="Glebas Diagnosticadas",
            style_function=estilo_talhao,
            tooltip=GeoJsonTooltip(fields=campos_tooltip, aliases=aliases_tooltip, localize=True),
            popup=GeoJsonPopup(fields=campos_popup, aliases=aliases_popup, localize=True, labels=True)
        )
        geojson_layer.add_to(m)

    # Legenda Flutuante de Diagnóstico
    legenda_html = """
    <div style="
        position: fixed; 
        bottom: 25px; 
        left: 25px; 
        width: 250px; 
        background-color: rgba(255, 255, 255, 0.95);
        border: 2px solid #bdc3c7;
        border-radius: 8px;
        z-index: 9999;
        font-size: 11px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        padding: 10px 14px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.18);
    ">
        <div style="font-weight: 700; margin-bottom: 6px; font-size: 12px; color: #2c3e50; border-bottom: 1px solid #e1e8ed; padding-bottom: 4px;">
            Diagnóstico de Cobertura
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <span style="background: #e74c3c; width: 13px; height: 13px; display: inline-block; border-radius: 3px; margin-right: 8px; border: 1px solid #c0392b;"></span>
            <span style="color: #2c3e50;"><b>Clareira Aberta</b> (Sev. Alta)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <span style="background: #f39c12; width: 13px; height: 13px; display: inline-block; border-radius: 3px; margin-right: 8px; border: 1px solid #d68910;"></span>
            <span style="color: #2c3e50;"><b>Dossel Ralo</b> (Sev. Moderada)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <span style="background: #2ecc71; width: 13px; height: 13px; display: inline-block; border-radius: 3px; margin-right: 8px; border: 1px solid #27ae60;"></span>
            <span style="color: #2c3e50;"><b>Regeneração em Curso</b></span>
        </div>
        <div style="display: flex; align-items: center; margin-top: 6px; padding-top: 5px; border-top: 1px dashed #d5dbdb;">
            <span style="border-top: 2px dashed #00ffff; width: 16px; display: inline-block; margin-right: 8px;"></span>
            <span style="color: #555; font-size: 10px;">Limite PES Charapucu</span>
        </div>
    </div>
    """
    m.get_root().html.add_child(Element(legenda_html))

    folium.LayerControl(position="topright", collapsed=False).add_to(m)
    return m
