---
name: relatorio-tecnico-ngeo
description: Gerador automatizado de Relatórios Técnicos e Folhas de Despacho (PAe/SEI) do Núcleo de Geotecnologias (NGEO/IDEFLOR-Bio). Processa autos administrativos (PDFs de ofícios, memorandos e despachos), tria os dados geoespaciais necessários e preenche o template Word oficial mantendo cabeçalho com logotipo institucional, tipografia Arial 12, alinhamento justificado e espaçamento 1,5 entrelinhas.
---

# Skill: Gerador de Relatório Técnico e Despacho NGEO/IDEFLOR-Bio

Esta skill implementa o fluxo oficial de elaboração de **Relatórios Técnicos** e **Folhas de Despacho** para o Núcleo de Geotecnologias (NGEO) do IDEFLOR-Bio, integrando a ingestão de autos administrativos, o processamento de dados geoespaciais e a geração documental padronizada.

---

## 1. Princípios Institucionais e Diretrizes de Redação

* **Papel Institucional do NGEO:** O NGEO é um órgão técnico provedor de **subsídios geoespaciais e cartográficos auditados**, e não tomador de decisões de mérito administrativo ou enquadrador de políticas públicas. A redação deve ser rigorosamente técnica, neutra e amparada em dados oficiais (DETER, PRODES, SICAR, DGMUC), sem juízos de valor.
* **Terminologia de Sensoriamento Remoto:** Utilizar termos limpos e institucionais como *"por meio de imagens orbitais do sensor Sentinel-2"* ou *"imagens orbitais Sentinel-2"*. Provedores específicos de mosaicos (ex.: EOX IT Services GmbH, ESA Copernicus) não devem poluir o corpo do texto metodológico, devendo constar exclusivamente na seção final de **Referências (norma ABNT)**.
* **Sem Jargões Comerciais ou de Conversa:** Nunca incluir especificações de venda ou menções informais no relatório (evitar termos como *"formato A4 Paisagem em alta resolução de 300 DPI e PDF vetorial"* ou *"padrão do QGIS"*). Utilizar simplesmente: **"prancha cartográfica institucional padronizada"**. O mapa oficial segue anexo ao processo.
* **Limitações do Sistema PAe e Envio de Vetores:** Como o sistema de processo eletrônico do Estado do Pará (PAe) só suporta anexos em formato PDF, deve-se explicitar no relatório e no despacho que a prancha cartográfica impressa/gerada segue anexa em PDF, enquanto os arquivos vetoriais digitais (Shapefile / GeoPackage) são disponibilizados/encaminhados via correio eletrônico institucional (e-mail).

---

## 2. Padrões Formais e Tipográficos Obrigatórios

Para todos os documentos Word (`.docx`) gerados:

* **Documento Matriz (Template):** Deve ser carregado a partir de `relatorio.docx` oficial (ex.: `H:\Meu Drive\DEV\layout_extraido_qgis\relatorios\relatorio.docx`), garantindo a preservação absoluta do `header1.xml` e da imagem com as logomarcas institucionais (`image1.png`).
* **Tipografia Padrão:** **Arial**.
* **Tamanho do Corpo de Texto:** **12 pt**.
* **Alinhamento do Corpo de Texto:** **Justificado** (`WD_ALIGN_PARAGRAPH.JUSTIFY`).
* **Espaçamento Entrelinhas:** **1,5 linhas** (`line_spacing = 1.5`).
* **Títulos e Seções Numeradas:** Arial 12 pt Negrito, alinhamento à esquerda, espaçamento entrelinhas simples (1.15) e recuo após de 4 a 6 pt.
* **Título Principal:** Arial 14 pt Negrito.
* **Tabelas Internas:** Arial 9,5 a 10 pt, estilo `Table Grid`.
* **Assinatura:** Centralizada, com nome em caixa alta negrito, cargo e instituição.

---

## 3. Estrutura Padrão do Relatório Técnico

```text
RELATÓRIO TÉCNICO
[Título Específico do Diagnóstico ou Parecer]

1. Identificação do Documento
   • Nº do Protocolo: [Processo nº YYYY/XXXXXX]
   • Elaboração: Samuel da Costa dos Santos – Coordenador do NGEO
   • Demandante: [Gerência / Diretoria / Órgão solicitante]
   • Data: [Data de emissão]

2. Objetivos
   [Descrição do fornecimento de subsídios geoespaciais em atendimento aos autos]

3. Contextualização
   [Histórico administrativo, documentos de encaminhamento (memorando/ofício),
    enquadramento legal das UCs (decretos) e características físicas da região]

4. Procedimentos Realizados
   [Ambiente SIG, geodésia SIRGAS 2000 UTM, fontes primárias homologadas,
    conferência por imagens orbitais Sentinel-2 e geração da prancha cartográfica]

5. Resultados
   5.1 Síntese Espacial das Glebas / Ocorrências Mapeadas
   [Tabela 1: Identificador NGEO, área calculada e acesso/localização]
   5.2 [Seção Analítica Dinâmica / Atributos Oficiais]
   [Tabela 2: Atributos homologados na base oficial (ex.: DETER/INPE com GID, data, sensor,
    órbita/ponto; ou sobreposição de imóvel/CAR com zoneamento/UC)]
   * A skill deve consultar o usuário sobre os dados específicos para esta seção.

6. Conclusão e Encaminhamento
   [Formalização de atendimento, prancha cartográfica anexa em PDF e
    aviso de disponibilização dos arquivos vetoriais via e-mail institucional]

7. Referências
   [Citações bibliográficas e bases de dados padronizadas na norma ABNT]

[Assinatura Centralizada]
SAMUEL DA COSTA DOS SANTOS
Coordenador do Núcleo de Geotecnologias – NGEO
Instituto de Desenvolvimento Florestal e da Biodiversidade do Estado do Pará – IDEFLOR-Bio
```

---

## 4. Padrão da Folha de Despacho (`despacho.txt`)

O despacho de devolução para o sistema eletrônico (PAe / SEI) deve ser objetivo e formal:
* **Destino:** A autoridade ou gerência que assinou o último despacho de encaminhamento (ex.: DGMUC, GRX).
* **Regra de Ouro:** Não duplicar as tabelas e dados analíticos do relatório técnico.
* **Conteúdo:** Restituição dos autos informando o atendimento técnico com juntada do Relatório Técnico e da prancha cartográfica em PDF, indicando o envio dos vetores por e-mail institucional.
