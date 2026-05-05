# Goiás Verde Streamlit

> Aplicación web open-source para análisis exploratorio de datos y
> aprendizaje automático de flujos de gases de efecto invernadero (GEI)
> del suelo medidos con analizadores de gases traza a láser portátiles
> usando espectroscopía OF-CEAS (LI-COR LI-7810SC para CH₄/CO₂/H₂O +
> Smart Chamber 8200-01S, y LI-7820 para N₂O/H₂O).

[English](./README.md) | [Português](./README.pt.md) | [Español](./README.es.md)

**Versión:** 1.0  
**Autores:** Souza, L. R. da S. et al.  
**Licencia:** GPLv2 con cláusula de citación obligatoria — vea [LICENSE](./LICENSE).

---

## Visión general

`goias-verde-streamlit` consolida en una única aplicación web todo el flujo
de análisis de GEI con cámara estática: ingestión de archivos CSV/XLSX
generados por analizadores de gases traza a láser (como la serie LI-COR
LI-78xx, que usa espectroscopía OF-CEAS en lugar de la técnica de
absorción infrarroja de los IRGAs tradicionales), pipeline configurable
de limpieza, análisis exploratorios, regresión bivariada y regresión
supervisada. La aplicación forma parte de
la iniciativa **Goiás Verde** del *Instituto Federal Goiano – Campus Rio
Verde* y del *Centro de Excelencia en Agricultura Exponencial (CEAGRE)*.
Está escrita en Python con [Streamlit](https://streamlit.io) y es agnóstica
al dataset: cualquier hoja tabular que se ajuste al esquema de una campaña
de flujo de GEI con cámara puede ser analizada.

## Características

1. **Carga** — CSV/XLSX con selección de hoja y caché en memoria.
2. **Pipeline** — Cinco filtros configurables con reporte transparente de
   etapas: remoción de variables, filtro diagnóstico, umbral de R²,
   outliers por cuantiles y por grupo, agregación de réplicas (media/mediana).
3. **EDA** — Nueve pestañas: resumen estadístico, calidad de los datos,
   distribuciones univariadas, boxplots/violins, matriz de dispersión,
   mapa de correlación, mapa espacial, **serie temporal de flujos** y
   **composición categórica**.
4. **Regresión** — Presets bivariados, incluyendo el preset de
   **sensibilidad térmica Q₁₀** (van 't Hoff) usado en la literatura de
   flujos del suelo, más bloque totalmente personalizable con hue y facet.
5. **Modelado** — Regresión supervisada con cinco estimadores (Linear,
   Random Forest, Gradient Boosting, Decision Tree, KNN), holdout +
   validación cruzada, **gráfico predicho vs. observado** y barra de
   importancia de features.
6. **Autenticación** — Capa opcional de login vía Supabase para uso
   institucional.
7. **i18n** — Selector de idioma para **Portugués / Inglés / Español**.

## Requisitos

- Python 3.10
- Dependencias listadas en [`requirements.txt`](./requirements.txt).

## Instalación

```bash
python3.10 -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -U pip wheel
pip install -r requirements.txt
```

## Cómo ejecutar

```bash
python -m streamlit run app.py
```

> Use siempre `python -m streamlit` para garantizar que se utilice el
> Streamlit del `.venv`.

## Cómo correr los tests

```bash
pytest tests/ -v
```

## Dataset de muestra

Un dataset sintético (240 filas × 24 columnas) que replica el esquema del
LI-COR LI-7810SC + Smart Chamber está
disponible en [`data/sample/`](./data/sample/). Para regenerarlo:

```bash
cd data/sample
python generate_sample.py
```

## Internacionalización

Para agregar un nuevo idioma, cree `src/i18n/locales/<código>.json` con las
mismas llaves que `pt.json`, registre el código en
`src/i18n/translations.py::AVAILABLE_LANGUAGES` y valide con:

```bash
python -m scripts.i18n_audit
```

Guía completa en [`docs/i18n.md`](./docs/i18n.md).

## Autenticación Supabase (opcional)

Para activar el login:

1. Copie `.streamlit/secrets.toml.example` a `.streamlit/secrets.toml`.
2. Complete `url` y `publishable_key` de su proyecto Supabase.
3. Reinicie el app.

Guía completa en [`docs/deployment.md`](./docs/deployment.md).

## Licencia

Este proyecto está licenciado bajo la **GNU General Public License
versión 2** o posterior, **con cláusula de citación obligatoria**.
Cualquier uso académico o comercial del software debe citar la
publicación referenciada abajo. Vea [LICENSE](./LICENSE) para el texto
completo.

## Citación

Si usa este software en su investigación, **debe citar la publicación**:

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

GitHub también muestra un botón "Cite this repository" vía [`CITATION.cff`](./CITATION.cff).

## Soporte

Para dudas o problemas, abra un issue en GitHub o contacte a
**leandrorodrigues.s@gmail.com**.

## Agradecimientos

Este trabajo contó con el apoyo de CNPq, CAPES, FAPEMIG, FAPEG, del
Instituto Federal de Educación, Ciencia y Tecnología Goiano (IF Goiano –
Campus Rio Verde y Campus Cristalina) y del Centro de Excelencia en
Agricultura Exponencial (CEAGRE).
