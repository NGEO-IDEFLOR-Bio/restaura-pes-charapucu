---
name: relatorio-tecnico-ngeo
description: Gerador automatizado de Relatórios Técnicos e Folhas de Despacho (PAe/SEI) do Núcleo de Geotecnologias (NGEO/IDEFLOR-Bio). Processa autos administrativos (PDFs de ofícios, memorandos e despachos), tria os dados geoespaciais necessários e preenche o template Word oficial mantendo cabeçalho com logotipo institucional, tipografia Arial 12, alinhamento justificado e espaçamento 1,5 entrelinhas.
---

# Skill: Gerador de Relatório Técnico e Despacho NGEO/IDEFLOR-Bio

Esta skill implementa o fluxo oficial de elaboração de **Relatórios Técnicos** e **Folhas de Despacho** para o Núcleo de Geotecnologias (NGEO) do IDEFLOR-Bio, integrando a ingestão de autos administrativos, o processamento de dados geoespaciais e a geração documental padronizada.

---

## 1. Padrões Formais e Tipográficos Obrigatórios

Para todos os documentos Word (`.docx`) gerados sob esta rotina:

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

## 2. Estrutura Padrão do Relatório Técnico

O relatório técnico deve seguir estritamente as seguintes seções:

```text
RELATÓRIO TÉCNICO
[Título Específico do Diagnóstico ou Parecer]

1. Identificação do Documento
   • Nº do Protocolo: [Processo nº YYYY/XXXXXX]
   • Elaboração: Samuel da Costa dos Santos – Coordenador do NGEO
   • Demandante: [Gerência / Diretoria / Órgão solicitante]
   • Data: [Data de emissão]

2. Objetivos
   [Descrição clara do escopo do levantamento em atendimento aos autos]

3. Contextualização
   [Enquadramento institucional, atos legais, decretos de criação de UCs,
    fundamentação dos memorandos/ofícios e critérios de programas como PRVN-PA]

4. Procedimentos Realizados
   [Metodologia em SIG, geodésia SIRGAS 2000 UTM, fontes oficiais (INPE, SICAR,
    DGMUC), filtros de qualidade e pranchas cartográficas geradas]

5. Resultados
   5.1 Detalhamento das Glebas / Polígonos
   [Tabela 1: Caracterização individualizada das feições]
   5.2 Enquadramento Institucional e Técnico
   [Tabela 2: Balanço de metas, áreas auditadas e superávits]

6. Conclusão e Encaminhamento
   [Parecer conclusivo e formalização de remessa dos autos ao demandante]

[Assinatura Centralizada]
SAMUEL DA COSTA DOS SANTOS
Coordenador do Núcleo de Geotecnologias – NGEO
Instituto de Desenvolvimento Florestal e da Biodiversidade do Estado do Pará – IDEFLOR-Bio
```

---

## 3. Padrão da Folha de Despacho (`despacho.txt`)

O despacho de devolução para o sistema eletrônico (PAe / SEI) deve ser objetivo e formal:
* **Destino:** A autoridade ou gerência que assinou o último despacho de encaminhamento (ex.: DGMUC, GRX, etc.).
* **Regra de Ouro:** Não duplicar as tabelas e dados analíticos do relatório técnico.
* **Conteúdo:** Informar a conclusão técnica dos trabalhos, a juntada do Relatório Técnico e da prancha cartográfica oficial, e colocar o núcleo à disposição para alinhamentos complementares.

```text
FOLHA DE DESPACHO

PROCESSO: [Nº do Processo]
ORIGEM: NGEO – Núcleo de Geotecnologias / IDEFLOR-Bio
DESTINO: [Diretoria / Gerência de Destino]
ASSUNTO: Devolução de Processo com Atendimento Técnico (Relatório Técnico e Prancha Cartográfica)
REFERÊNCIA: [Documentos do Processo]

À [Sigla do Destinatário],

Cumprimentando-os cordialmente, e em atenção ao [Documento de Origem] nos autos do Processo nº [XXXX/XXXXXXX], restituímos os presentes autos a esta [Diretoria/Gerência] informando o integral atendimento técnico à solicitação.

Para subsidiar [finalidade da demanda], fazemos a juntada aos autos do Relatório Técnico conclusivo e da respectiva prancha cartográfica oficial (padrão QGIS em alta resolução e PDF vetorial), acompanhada dos arquivos geoespaciais correspondentes.

Permanecemos à disposição para eventuais alinhamentos técnicos complementares.

Respeitosamente,


SAMUEL DA COSTA DOS SANTOS
Coordenador do Núcleo de Geotecnologias – NGEO
Instituto de Desenvolvimento Florestal e da Biodiversidade do Estado do Pará – IDEFLOR-Bio
```
