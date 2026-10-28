# Diretrizes Técnicas de Projeto: Banco de Áreas Aptas à Restauração Florestal — PES Charapucu

---

## 1. Visão Geral e Estratégia Institucional

* **Órgão Executor:** Núcleo de Geotecnologias (NGEO) / Instituto de Desenvolvimento Florestal e da Biodiversidade do Estado do Pará (IDEFLOR-Bio).
* **Finalidade Estratégica:** Estruturar um **Banco Qualificado de Áreas Elegíveis para Restauração Florestal** no Parque Estadual Charapucu (Marajó/PA). O objetivo não é travar em 130 hectares, mas **demonstrar musculatura técnica e inventário excedente**, permitindo ao órgão disputar editais, termos de cooperação e captação de recursos com uma carteira auditada de dezenas/centenas de hectares prontos para intervenção.
* **Entregável Chave em Colab:** Um notebook orquestrador contendo um **Mini-Dashboard Interativo** com cards de KPIs dinâmicos (área total filtrada, contagem de talhões, método dominante), gráficos analíticos e mapa temático reativo a filtros de atributos.

---

## 2. Arquitetura da Solução e Estrutura do Repositório

Seguindo o padrão desacoplado validado nos projetos anteriores do NGEO:

```text
├── data/
│   ├── raw/                 # Limite oficial DGMUC, hidrografia refinada, PRODES, MapBiomas
│   ├── reference/           # Hidrovias navegáveis, comunidades e bases operacionais
│   └── processed/           # Camadas limpas, sem corpos hídricos e polígonos classificados
├── src/
│   ├── 01_ingestao_mascaras.py     # Limpeza topológica, remoção de hidrografia/maré e união
│   ├── 02_analise_espectral.py     # Composição Sentinel-2/Planet, NDVI, NDWI e ΔNDVI
│   ├── 03_estratificacao_talhoes.py# Agrupamento, cálculo métrico e tipificação metodológica
│   └── 04_dashboard_components.py  # Funções construtoras dos widgets, mapa e gráficos
├── notebooks/
│   └── dashboard_charapucu.ipynb   # Interface interativa executável no Google Colab
├── outputs/
│   ├── vetores/             # GeoPackage e Shapefiles da carteira total e estratificada
│   └── relatorios/          # Tabelas consolidadas por classe de tamanho e método
├── config.yml               # Parâmetros de classificação, buffers e CRS
├── requirements.txt         # Dependências do ambiente Python
└── README.md
```

---

## 3. Parâmetros Cartográficos e Geodésicos

* **CRS de Trabalho e Métricas:** Projetar obrigatoriamente para `SIRGAS 2000 / UTM zone 22N` (`EPSG:31988`) antes de qualquer cálculo de área ($ha$), raio de compacidade ou distância métrica aos furos navegáveis.
* **CRS de Visualização e Web:** Converter para `SIRGAS 2000` Geográfico (`EPSG:4674`) ou `WGS 84` (`EPSG:4326`) exclusivamente no momento de alimentar o mapa interativo.

---

## 4. Metodologia de Identificação e Estratificação da Carteira

### 4.1 Mascaramento e Exclusão Hidrológica
1. **Recorte no Polígono Oficial:** DGMUC/IDEFLOR-Bio do PES Charapucu.
2. **Histórico Antrópico:** União espacial das áreas abertas PRODES Amazônia + classes de uso/cobertura antrópica e transição do MapBiomas.
3. **Máscara de Alta Resolução de Vias Úmidas e Maré:** Exclusão rigorosa da hidrografia (rios, furos, igarapés e canais de maré periódica) para eliminar falsos positivos de solo exposto/sedimentos em orlas de várzea.

### 4.2 Dinâmica de Regeneração e Método Indicado
Cálculo multitemporal espectral via Sentinel-2 (L2A) ou Planet NICFI:
* **$\Delta\text{NDVI} > 0.15$ (Ganho de biomassa consistente):**  
  $\rightarrow$ **Regeneração Natural Assistida (RNA)** / Condução de regenerantes (baixo custo de implantação).
* **$\Delta\text{NDVI} \in [-0.05, 0.15]$ (Vegetação herbácea/invasora ou estagnada):**  
  $\rightarrow$ **Enriquecimento Florestal** / Adensamento de espécies de várzea (açaí nativo, virola, mutamba, etc.).
* **$\Delta\text{NDVI} < -0.05$ ou NDVI baixo persistente (Solo compactado / pasto sujo degradado):**  
  $\rightarrow$ **Plantio Direto** / Restauração Ativa plena.

### 4.3 Classes de Porte e Logística (Estratificação da Carteira)
Os talhões identificados devem ser categorizados em atributos estruturados:

| Atributo | Classes / Categorias | Objetivo Operacional |
| :--- | :--- | :--- |
| **Classe de Área** | Pequeno ($< 5\text{ ha}$)<br>Médio ($5 - 20\text{ ha}$)<br>Grande ($20 - 50\text{ ha}$)<br>Macro-gleba ($> 50\text{ ha}$) | Permite ao gestor montar cestas que alcancem os 130 ha com poucos polígonos grandes ou com mosaico de pequenos |
| **Acesso Fluvial** | Alta acessibilidade ($< 200\text{ m}$ da margem navegável)<br>Média ($200 - 800\text{ m}$)<br>Baixa ($> 800\text{ m}$) | Viabilidade de desembarque de mudas e equipes por voadeiras |
| **Intervenção** | `RNA`, `Enriquecimento`, `Plantio Direto` | Estimativa orçamentária do projeto |

---

## 5. Especificação do Mini-Dashboard no Google Colab

O notebook `dashboard_charapucu.ipynb` funcionará como uma aplicação analítica independente em execução no Colab, composta por:

### 5.1 Painel de Controle (Filtros Interativos via `ipywidgets`)
* **Slider duplo de Área ($ha$):** Limite mínimo e máximo de área do talhão.
* **Dropdown/Multiselect de Métodos:** Selecionar um ou mais métodos (`RNA`, `Enriquecimento`, `Plantio Direto`).
* **Dropdown de Acessibilidade Fluvial:** Filtrar por distância à calha navegável.
* **Botão "Resetar Filtros" e Botão "Exportar Seleção Corrente".**

### 5.2 Linha de Cards de KPI (Atualização em Tempo Real)
* **Card 1:** Área Total Selecionada ($ha$) — com indicador visual comparativo à meta básica (ex.: *185 ha disponíveis — 142% da meta de 130 ha*).
* **Card 2:** Número de Talhões/Polígonos Selecionados.
* **Card 3:** Distância Média até a Margem Navegável ($m$).
* **Card 4:** Método Predominante na seleção corrente.

### 5.3 Painel Central: Gráficos Dinâmicos (`plotly` / `altair`)
* **Gráfico de Barras/Histograma:** Distribuição da área selecionada por classe de tamanho.
* **Gráfico de Rosca/Donut:** Proporção percentual da área por método de restauração sugerido.

### 5.4 Mapa Interativo Reativo (`folium` / `leafmap`)
* Renderização dos polígonos coloridos por **Método de Intervenção** ou **Classe de Tamanho**.
* Camada WMS/vetorial de fundo: Limite do PES Charapucu, hidrografia principal e pontos de apoio ribeirinho.
* **Popups ricos ao clicar no talhão:**
  * ID da Gleba
  * Área calculada ($ha$)
  * Método recomendado
  * Furo/Rio navegável mais próximo e distância ($m$)
  * Coordenadas centrais (Lat/Lon SIRGAS 2000)

### 5.5 Ação de Exportação Direta
* Widget com botão que extrai o subconjunto filtrado na tela e salva automaticamente em `outputs/vetores/` no formato `.gpkg` e `.csv`, gerando link para download direto no próprio Colab.

---

## 6. Diretrizes Técnicas para Agentes de Código e IA

1. **Reatividade Enxuta:** Não recarregar o GeoDataFrame a cada clique. Carregue o arquivo consolidado em memória uma única vez e realize filtros vetoriais diretamente sobre o `gdf` usando máscaras booleanas do Pandas/GeoPandas.
2. **Topologia Limpa:** Antes de exportar a base final, aplicar `shapely.validation.make_valid` e remover geometrias degeneradas ou com área nula.
3. **Robustez no Colab:** Usar dependências puras que não necessitem de reinicialização de servidor web externo (`ipywidgets`, `leafmap` ou `folium`, `plotly`). A visualização deve renderizar diretamente no output da célula do notebook.
```

O arquivo define a mudança de postura institucional (banco de áreas com inventário qualificado excedente) e especifica os componentes funcionais do dashboard reativo para o Colab.