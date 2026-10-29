---
name: qgis-layout-engine
description: >-
  Motor cartográfico para geração e reprodução automatizada de layouts padrão QGIS em Python e Google Colab.
  Estrutura pranchas A4 Paisagem (297 x 210 mm) com precisão milimétrica e hierarquia de três mapas:
  1) Localização Macro (Pará no contexto dos estados e países vizinhos);
  2) Localização Intermediária (Ocorrência no contexto da UC);
  3) Mapa Principal (Zoom de detalhe no alvo com mosaico Sentinel-2 Cloudless EOX ou GEE).
  Inclui caixas de moldura, seta norte, escalas gráficas calculadas, legendas convencionadas, notas SIRGAS 2000 e logotipos institucionais.
---

# QGIS Cartographic Layout Engine (Python / Google Colab)

Este módulo automatiza a produção de pranchas cartográficas institucionais no padrão do **Núcleo de Geotecnologias (NGEO/IDEFLOR-Bio)** sem depender da interface gráfica do QGIS, permitindo execução em scripts Python locais, pipelines de backend e notebooks do Google Colab.

O motor replica milimetricamente as posições, dimensões e proporções extraídas do arquivo `layout_elements.json` (gerado a partir de templates `.qpt` do QGIS).

---

## 1. Princípios e Hierarquia Cartográfica em 3 Níveis

O layout é construído em uma folha **A4 Paisagem ($297 \times 210\text{ mm}$)** e organiza a percepção espacial em três escalas articuladas:

```mermaid
flowchart TD
    subgraph MACRO["1. Localização Macro (Inferior Direito - 98 x 70 mm)"]
        M1["Estado do Pará em Destaque (#D5F5E3 / #1E8449)<br/>• Estados vizinhos (#EAEDED: AM, MT, TO, MA, AP, RR)<br/>• Países vizinhos (Suriname, Guiana Francesa) & Oceano Atlântico<br/>• UC em destaque com marcador vermelho e halo circular<br/>• Grade com snap em 5° e eixo Y a 90°"]
    end

    subgraph INTERMEDIARIO["2. Localização Intermediária (Superior Direito - 98 x 70 mm)"]
        I1["Contexto da Unidade de Conservação<br/>• Limite integral da UC em verde florestal (#D4EFDF / #1E8449)<br/>• Contexto municipal/hidrográfico (Afuá, rios e baías ao fundo)<br/>• Ocorrência em destaque com ponto de chamada e seta indicativa<br/>• Grade com snap em 0.10° e eixo Y a 90°<br/>• Dimensões idênticas ao mapa macro (98 x 70 mm)"]
    end

    subgraph DETALHE["3. Mapa Principal de Detalhe (Esquerda - 155 x 127.2 mm)"]
        D1["Enquadramento Focado no Alvo<br/>• Proporção idêntica à do retângulo externo (aspect ratio exato)<br/>• A imagem de satélite preenche 100% da área da grade (zero margem interna)<br/>• Snap da grade a valores redondos (0.010°)<br/>• Supressão de rótulos dos cantos (evita sobreposição X/Y e transbordamento)<br/>• Feição grande: rótulo minimalista com halo<br/>• Feição pequena: rótulo deslocado com seta indicativa (não cobre o polígono)<br/>• Eixo Y com coordenadas no sentido vertical ascendente (90°)"]
    end

    MACRO --> INTERMEDIARIO
    INTERMEDIARIO --> DETALHE
```

---

## 2. Padrões de Diagramação e Convenções Cartográficas

1. **Alinhamento do Mapa Principal e Margens Homogêneas:**
   * A janela cartográfica principal possui a mesma proporção geométrica de sua moldura externa (`155.0 / 127.2 \approx 1{,}2185`).
   * A imagem de satélite cobre 100% do interior da grade, sem qualquer faixa de margem interna entre o raster e as linhas de coordenadas.
2. **Snap da Grade e Supressão de Rótulos de Canto:**
   * Todas as grades de coordenadas possuem snap travado em valores redondos e cheios (`0.01°` no principal, `0.10°` no intermediário, `5°` no macro).
   * Rótulos muito próximos dos cantos são automaticamente suprimidos para eliminar colisão entre números de latitude e longitude nas quinas e evitar transbordamento da moldura.
3. **Harmonia dos Mapas de Apoio (Dimensões Idênticas):**
   * Tanto o mapa de *Localização da Ocorrência na UC* quanto o de *Localização da Unidade no Pará* possuem **dimensões rigorosamente idênticas ($98{,}0 \times 70{,}0\text{ mm}$)**.
   * Títulos simples diretos e sem subtítulos desnecessários.
4. **Rótulos Minimalistas e com Tratamento Diferenciado de Escala:**
   * Feição grande ($> 20\text{ ha}$): rótulo centralizado minimalista com halo protetor.
   * Feição pequena ($< 20\text{ ha}$): rótulo deslocado externamente com linha/seta dourada apontando para o centroide, mantendo 100% da feição visível sobre a imagem de satélite.
5. **Orientação dos Rótulos no Eixo Y (Vertical Ascendente):**
   * Em **todos os 3 mapas**, os textos de latitude no eixo Y estão posicionados com rotação de **90° (sentido vertical ascendente)**, acompanhando paralelamente a moldura e poupando espaço horizontal.
6. **Centralização da Seta Norte e Barra de Escala:**
   * Ambos os elementos técnicos estão centralizados no eixo horizontal de simetria do bloco técnico ($x_{\text{center}} = 145{,}976\text{ mm}$).
7. **Legenda Completa das Camadas da Prancha:**
   * A legenda contempla as feições ativas em toda a composição:
     - Área de Corte Raso Auditada (DETER/INPE - 183,76 ha)
     - Limite do Parque Estadual Charapucu (72.506 ha)
     - Limite do Estado do Pará (Contexto Regional)
     - Corpos Hídricos & Várzea Estuarina (Baía Vieira Grande)

---

## 3. Elementos do Layout Cadastrados

| Item ID | Descrição | $x\text{ (mm)}$ | $y\text{ (mm)}$ | $w\text{ (mm)}$ | $h\text{ (mm)}$ | Tipo / Função |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| `txt_titulo` | Cabeçalho / Título Principal | 8.000 | 5.411 | 278.850 | 12.302 | Faixa com título oficial em caixa alta |
| `rec_mapa` | Moldura Externa do Mapa Principal | 8.150 | 14.108 | 167.106 | 137.143 | Retângulo de contenção |
| `mapa_geral` | Mapa Principal (Satélite + Vetor) | 14.150 | 18.000 | 155.000 | 127.200 | Viewport proporcional com grade ancorada |
| `rec_localizacao`| Painel Direito de Enquadramento | 175.254 | 14.108 | 111.466 | 184.402 | Painel para os dois mapas de apoio |
| `mapa_localizacao_imovel`| Inset Superior (Alvo na UC) | 182.000 | 23.000 | 98.000 | 70.000 | Contexto regional com coordenadas (98 x 70 mm) |
| `mapa_localizacao_unidade`| Inset Inferior (UC no Pará) | 182.000 | 110.500 | 98.000 | 70.000 | Contexto macro estadual (98 x 70 mm) |
| `rec_legenda` | Caixa de Legenda | 8.150 | 151.251 | 108.543 | 32.883 | Legenda completa de todas as feições |
| `rec_fonte` | Caixa de Metadados e Fontes | 8.150 | 184.135 | 108.543 | 14.375 | SIRGAS 2000, insumo EOX e notas |
| `rec_escala-icons-seta` | Caixa de Escala, Norte e Logos | 116.697 | 151.251 | 58.559 | 47.259 | Bloco técnico e institucional |
| `seta_norte` | Rosa dos Ventos / Norte | 140.476 | 153.200 | 11.000 | 13.000 | Vetor centralizado horizontalmente |
| `barra_escala` | Escala Gráfica e Numérica | 129.976 | 168.000 | 32.000 | 10.000 | Barra centralizada no mesmo eixo |
| `logo_ngeo` | Logotipo NGEO | 121.500 | 181.500 | 12.500 | 14.500 | Imagem institucional PNG |
| `logo_ideflorbio`| Logotipo IDEFLOR-Bio | 137.000 | 181.500 | 17.500 | 14.500 | Imagem institucional PNG |
| `logo_estado_para`| Brasão do Estado do Pará | 158.000 | 181.500 | 13.500 | 14.500 | Brasão oficial do Pará PNG |

---

## 4. Como Usar em Novos Projetos

```python
import geopandas as gpd
from qgis_layout_engine import QGISLayoutEngine

# 1. Carregar as geometrias do projeto
gdf_alvo = gpd.read_file("caminho/para/alvo.geojson")
gdf_uc = gpd.read_file("caminho/para/uc.geojson")
gdf_estados = gpd.read_file("caminho/para/estados_brasileiros.shp")
gdf_paises = gpd.read_file("caminho/para/america_do_sul.shp")

# 2. Inicializar o motor
engine = QGISLayoutEngine()
engine.create_layout()
engine.draw_frames()

# 3. Textos, logos e notas técnicas
engine.draw_header_and_titles(
    titulo_mapa="MAPA DE DIAGNÓSTICO – PARQUE ESTADUAL CHARAPUCU"
)
engine.draw_metadata_and_sources()
engine.draw_logos("caminho/logo_ngeo.png", "caminho/logo_ideflor.png", "caminho/brasao_para.png")
engine.draw_north_arrow()

# 4. Renderizar a hierarquia dos três mapas
engine.render_macro_map(gdf_estados, gdf_paises, gdf_uc)
engine.render_intermediate_map(gdf_uc, gdf_alvo)
engine.render_main_map(gdf_alvo, gdf_uc=gdf_uc, eox_year="2025")

# 5. Legenda e exportação
engine.render_legend()
engine.export("outputs/mapas/mapa_layout_qgis.png", "outputs/mapas/mapa_layout_qgis.pdf", dpi=300)
```
