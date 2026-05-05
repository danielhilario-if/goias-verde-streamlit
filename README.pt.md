# Goiás Verde Streamlit

> Aplicação web open-source para análise exploratória de dados e aprendizado
> de máquina de fluxos de gases de efeito estufa (GEE) do solo medidos com
> analisadores de gases traço a laser portáteis usando espectroscopia
> OF-CEAS (LI-COR LI-7810SC para CH₄/CO₂/H₂O + Smart Chamber 8200-01S e
> LI-7820 para N₂O/H₂O).

[English](./README.md) | [Português](./README.pt.md) | [Español](./README.es.md)

**Versão:** 1.0  
**Autores:** Souza, L. R. da S. et al.  
**Licença:** GPLv2 com cláusula de citação obrigatória — veja [LICENSE](./LICENSE).

---

## Visão geral

O `goias-verde-streamlit` consolida em uma única aplicação web todo o fluxo
de análise de GEE com câmara estática: ingestão de arquivos CSV/XLSX
gerados por analisadores de gases traço a laser (como a série LI-COR
LI-78xx, que usa espectroscopia OF-CEAS em vez da técnica de absorção
infravermelha dos IRGAs tradicionais), pipeline configurável de limpeza,
análises exploratórias, regressão bivariada e regressão supervisionada. A aplicação faz parte da
iniciativa **Goiás Verde** do *Instituto Federal Goiano – Campus Rio Verde*
e do *Centro de Excelência em Agricultura Exponencial (CEAGRE)*. É escrita
em Python com [Streamlit](https://streamlit.io) e é agnóstica a dataset:
qualquer planilha tabular que se encaixe no esquema de uma campanha de
fluxo de GEE com câmara pode ser analisada.

## Funcionalidades

1. **Upload** — CSV/XLSX com seleção de aba e cache em memória.
2. **Pipeline** — Cinco filtros configuráveis com relatório transparente de
   etapas: remoção de variáveis, filtro diagnóstico, limiar de R²,
   outliers por quantis e por grupo, agregação de réplicas (média/mediana).
3. **EDA** — Nove abas: resumo estatístico, qualidade dos dados,
   distribuições univariadas, boxplots/violins, matriz de dispersão, mapa
   de correlação, mapa espacial, **série temporal de fluxos** e
   **composição categórica**.
4. **Regressão** — Presets bivariados, incluindo o preset de
   **sensibilidade térmica Q₁₀** (van 't Hoff) usado na literatura de
   fluxos de solo, mais bloco totalmente customizável com hue e facet.
5. **Modelagem** — Regressão supervisionada com cinco estimadores
   (Linear, Random Forest, Gradient Boosting, Decision Tree, KNN),
   holdout + validação cruzada, **gráfico predito vs. observado** e
   barra de importância das features.
6. **Autenticação** — Camada opcional de login via Supabase para uso
   institucional.
7. **i18n** — Seletor de idioma para **Português / Inglês / Espanhol**.

## Requisitos

- Python 3.10
- Dependências em [`requirements.txt`](./requirements.txt).

## Instalação

```bash
python3.10 -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -U pip wheel
pip install -r requirements.txt
```

## Como executar

```bash
python -m streamlit run app.py
```

> Use sempre `python -m streamlit` para garantir que o Streamlit do `.venv` é utilizado.

## Como rodar os testes

```bash
pytest tests/ -v
```

## Dataset de exemplo

Um dataset sintético (240 linhas × 24 colunas) que replica o esquema do
LI-COR LI-7810SC + Smart Chamber está
disponível em [`data/sample/`](./data/sample/). Para regenerar:

```bash
cd data/sample
python generate_sample.py
```

## Internacionalização

Para adicionar um novo idioma, crie `src/i18n/locales/<código>.json` com as
mesmas chaves de `pt.json`, registre o código em
`src/i18n/translations.py::AVAILABLE_LANGUAGES` e valide com:

```bash
python -m scripts.i18n_audit
```

Guia completo em [`docs/i18n.md`](./docs/i18n.md).

## Autenticação Supabase (opcional)

Para ativar o login:

1. Copie `.streamlit/secrets.toml.example` para `.streamlit/secrets.toml`.
2. Preencha `url` e `publishable_key` do seu projeto Supabase.
3. Reinicie o app.

Guia completo em [`docs/deployment.md`](./docs/deployment.md).

## Licença

Este projeto está licenciado sob a **GNU General Public License versão 2**
ou superior, **com cláusula de citação obrigatória**. Qualquer uso
acadêmico ou comercial do software deve citar a publicação referenciada
abaixo. Veja o arquivo [LICENSE](./LICENSE) para o texto completo.

## Citação

Se você usa este software em sua pesquisa, **deve citar a publicação**:

```bibtex
@article{Souza2025GoiasVerde,
  author  = {da Silva Souza, Leandro Rodrigues and Jakelaitis, Adriano and
             Alves da Silva, Daiane and Tonus Ribeiro, Caio and
             Hil{\'a}rio da Silva, Daniel and Alves Pereira, Adriano and
             de Oliveira Andrade, Adriano},
  title   = {{Goi{\'a}s Verde Streamlit}: An open-source web application
             for exploratory analysis and machine learning of soil
             greenhouse gas fluxes measured with portable laser-based
             trace gas analyzers},
  journal = {Software Impacts},
  year    = {2025},
  doi     = {10.1016/j.simpa.2025.XXXXXX}
}
```

O GitHub também exibe um botão "Cite this repository" via [`CITATION.cff`](./CITATION.cff).

## Suporte

Para dúvidas ou problemas, abra uma issue no GitHub ou contate
**leandrorodrigues.s@gmail.com**.

## Agradecimentos

Este trabalho contou com o apoio do CNPq, CAPES, FAPEMIG, FAPEG, do
Instituto Federal de Educação, Ciência e Tecnologia Goiano (IF Goiano –
Campus Rio Verde e Campus Cristalina) e do Centro de Excelência em
Agricultura Exponencial (CEAGRE).
