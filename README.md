# Diagnóstico Geoespacial de Desmatamento e Subsídios à Restauração Florestal — Parque Estadual Charapucu

**Instituto de Desenvolvimento Florestal e da Biodiversidade do Estado do Pará (IDEFLOR-Bio)**  
**Diretoria de Gestão e Monitoramento de Unidades de Conservação (DGMUC) / Núcleo de Geotecnologias (NGEO)**

---

## 1. Identificação do Processo e Objeto Institucional

* **Processo Administrativo:** Processo nº 2026/3611213 (PAe / SEI)
* **Documentos de Referência:** Memorando nº 04/ASSTEC e Despacho DGMUC
* **Unidade de Conservação (UC):** Parque Estadual Charapucu (PES Charapucu)
* **Ato Legal de Criação:** Decreto Estadual nº 2.592, de 09 de novembro de 2010
* **Categoria de Manejo:** Proteção Integral (SNUC / SEUC)
* **Localização Administrativa:** Município de Afuá, Região de Integração do Marajó, Estado do Pará
* **Finalidade Institucional:** Fornecimento de subsídios geoespaciais e cartográficos auditados para apoiar a identificação de áreas para Unidades Demonstrativas de Restauração Florestal, em consonância com as diretrizes do Plano de Recuperação da Vegetação Nativa do Estado do Pará (PRVN-PA).

---

## 2. Balanço Geral dos Resultados Auditados

A auditoria geoespacial processada diretamente em Python sob a base oficial do Sistema de Detecção do Desmatamento em Tempo Real (DETER / TerraBrasilis / INPE) identificou duas ocorrências contíguas de corte raso oficial (`DESMATAMENTO_CR`) no interior do Parque Estadual Charapucu:

| Parâmetro / Métrica | Valor Auditado | Observação Institucional |
| :--- | :---: | :--- |
| **Demanda Dimensional Mínima** | $130{,}00\text{ ha}$ | Parâmetro solicitado no Memorando nº 04/ASSTEC |
| **Área Total Mapeada e Auditada** | **$183{,}76\text{ ha}$** | Homologada na série histórica oficial do DETER/INPE |
| **Superávit Físico Disponível** | **$+53{,}76\text{ ha}$** | **$141{,}35\%$** da demanda dimensional mínima |
| **Número de Feições** | **2 glebas contíguas** | Atende ao critério de menor fragmentação territorial |
| **Localização / Acesso Fluvial** | Baía de Vieira Grande | Setor Leste da Ilha ($2{,}3\text{ km}$ e $3{,}2\text{ km}$ da calha) |
| **Cobertura Vegetal Atual** | Regeneração Secundária | Dossel fechado (sucessão ecológica há mais de 6 anos) |

---

## 3. Estrutura Enxuta do Repositório

O repositório foi simplificado e estruturado para execução direta em Python, eliminando dependências externas:

```text
levantamento-desmatamento-charapucu/
├── data/
│   ├── raw/                             # Camadas geoespaciais brutas oficiais
│   │   ├── limite_pes_charapucu.geojson # Limite oficial do Decreto nº 2.592/2010
│   │   ├── deter_alertas_charapucu.geojson # Polígonos homologados DETER/INPE
│   │   └── ucs_estaduais.geojson        # Base corporativa de UCs do IDEFLOR-Bio
│   └── processed/
│       └── limite_pes_charapucu_utm22n.gpkg # Limite oficial projetado em UTM 22N
├── src/
│   ├── 00_extracao_limite_pes_charapucu.py # Extração e validação geodésica do PES Charapucu
│   ├── 06_consolidar_deter_charapucu.py    # Auditoria métrica e atributos dos alertas DETER
│   ├── qgis_layout_engine.py               # Motor cartográfico de alta fidelidade padrão QGIS
│   └── 07_gerar_mapa_layout_qgis.py        # Executável para geração das pranchas oficiais
├── outputs/
│   ├── mapas/                           # Pranchas cartográficas institucionais
│   │   ├── mapa_layout_qgis_deter_charapucu.png # Imagem oficial em 300 DPI
│   │   └── mapa_layout_qgis_deter_charapucu.pdf # Prancha vetorial para anexar ao processo
│   ├── relatorios/                      # Peças documentais oficiais
│   │   ├── relatorio_tecnico_processo_2026_3611213.docx # Relatório Técnico oficial (Arial 12)
│   │   ├── relatorio_tecnico_processo_2026_3611213.pdf  # Versão assinada/pronta em PDF
│   │   ├── despacho_devolucao_processo_2026_3611213.txt # Folha de Despacho (PAe / SEI)
│   │   ├── tabela_geral_todas_glebas.csv    # Tabela cadastral detalhada das glebas
│   │   └── resumo_executivo_carteira.json   # Metadados consolidados da carteira
│   └── vetores/                         # Dados geográficos prontos para envio
│       ├── banco_restauracao_pes_charapucu.gpkg # GeoPackage em SIRGAS 2000 UTM 22N
│       └── banco_restauracao_pes_charapucu.geojson # Formato aberto para interoperabilidade
├── .agents/skills/                      # Skills reutilizáveis configuradas no projeto
│   ├── qgis-layout-engine/              # Skill de geração cartográfica padronizada QGIS
│   └── relatorio-tecnico-ngeo/          # Skill de geração de Relatórios e Despachos PAe
├── config.yml                           # Parâmetros de configuração e caminhos de dados
├── requirements.txt                     # Dependências mínimas de ambiente Python
└── README.md                            # Este documento
```

---

## 4. Parâmetros Geodésicos Adotados

* **Sistema Geodésico de Referência:** SIRGAS 2000 (*Sistema de Referência Geocêntrico para as Américas*).
* **Projeção Plana de Cálculo Métrico:** `SIRGAS 2000 / UTM zone 22N` (`EPSG:31988`). Todas as áreas planimétricas ($ha$), perímetros e distâncias logísticas foram calculadas sob este CRS.
* **Armazenamento e Interoperabilidade:** `SIRGAS 2000` Geográfico (`EPSG:4674`) e `WGS 84` (`EPSG:4326`).

---

## 5. Como Reproduzir os Produtos

Para reproduzir todos os produtos (mapas, métricas e relatórios) diretamente em terminal:

```bash
# 1. Consolidar os dados brutos e métricas oficiais do DETER
python src/06_consolidar_deter_charapucu.py

# 2. Gerar a prancha cartográfica oficial A4
python src/07_gerar_mapa_layout_qgis.py
```

---
*Núcleo de Geotecnologias (NGEO) — IDEFLOR-Bio*  
*Belém — Pará, 2026.*
