# ChamberFlux

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

`chamberflux` consolida en una única aplicación web todo el flujo
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

1. **Carga** — CSV/XLSX con selección de hoja, caché en memoria y
   **validación explícita del esquema** (columnas esperadas clasificadas
   en *requeridas*, *recomendadas* y *opcionales*; verificación de tipos,
   detección de centinelas como −9999, validación de Lat/Lon dentro de
   [-90,90]/[-180,180]). Las columnas ausentes no bloquean el uso —
   simplemente desactivan funcionalidades específicas.
2. **Pipeline** — Seis filtros configurables con reporte transparente de
   etapas: remoción de variables, filtro diagnóstico, umbral de R²,
   outliers por cuantiles (con agrupamiento opcional), **limpieza
   estacional robusta Q10–Q90** (por gas, por estación, con factor de
   cerco ajustable) y agregación de réplicas (media/mediana).
3. **EDA** — Doce pestañas: resumen estadístico, calidad de los datos,
   distribuciones univariadas, boxplots/violins, matriz de dispersión,
   **correlación Pearson / Spearman / Kendall**, mapa espacial, serie
   temporal, composición categórica, **inferencia (Kruskal-Wallis +
   normalidad Shapiro-Wilk / Anderson-Darling / D'Agostino-Pearson +
   VIF)**, **ranking de hotspots** y **detección multi-método de
   outliers** (Z-score · IQR · Isolation Forest · LOF · Elliptic
   Envelope con criterio de consenso ≥3).
4. **Regresión** — Presets bivariados, incluyendo el preset de
   **sensibilidad térmica Q₁₀** (van 't Hoff) usado en la literatura de
   flujos del suelo, más bloque totalmente personalizable con hue y facet.
5. **Modelado** — Regresión supervisada con cinco estimadores (Linear,
   Random Forest, Gradient Boosting, Decision Tree, KNN), holdout +
   validación cruzada, gráfico predicho vs. observado y barra de
   importancia de features.
6. **Análisis Espacial** — Seis pestañas: **interpolación IDW**,
   **Moran's I global + LISA local** (HH/LL/HL/LH/NS), **Getis-Ord G\***
   para detección de hotspots significativos, **agregación en grilla
   UTM** regular (1 km por defecto), **kriging ordinario** con
   variograma esférico ajustado, y **basemap de Rio Verde** vía `geobr`.
7. **Serie Temporal** — Agregación diaria (media/mediana) y
   **descomposición STL** (tendencia + estacionalidad + residuo) con
   período estacional configurable y métricas de fuerza de tendencia y
   estacionalidad.
8. **Comparación por grupo** — Página configurable (preset opcional
   *Mata × Otros* para la cuestión Mata-vs-Cropland; acepta cualquier
   partición de cualquier columna categórica): media ± SE y mediana por
   grupo, **test de Mann-Whitney U**, **regresión log-lineal
   $\log(Y) \sim X$ por grupo** con Y y X elegidos por el usuario, y
   perfil **horario con flujo acumulativo**.
9. **Autenticación** — Capa opcional de login vía Supabase para uso
   institucional.
10. **i18n** — Selector de idioma para **Portugués / Inglés / Español**.

## Requisitos

- Python 3.10+
- Dependencias listadas en [`requirements.txt`](./requirements.txt):
  - **Núcleo**: Streamlit, pandas, NumPy, Matplotlib, seaborn,
    scikit-learn, openpyxl, Supabase.
  - **Estadística**: scipy, statsmodels (STL, VIF, tests de normalidad).
  - **Geoespacial**: geopandas, shapely, geobr (límites municipales
    brasileños), libpysal (pesos espaciales KNN), esda (Moran's I,
    LISA, Getis-Ord G\*).

> En Windows, geopandas/geobr/libpysal/esda dependen de GDAL. Si el
> `pip install` falla para esos paquetes, considere usar Conda
> (`conda install -c conda-forge geopandas libpysal esda`) o un wheel
> de GDAL pre-compilado.

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

Si además quiere regenerar las figuras del manuscrito con los scripts
de captura basados en Playwright en `data/sample/`, instale las
dependencias de desarrollo:

```bash
pip install -r requirements-dev.txt
playwright install chromium
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
@article{Souza2026ChamberFlux,
  author  = {Souza, Leandro Rodrigues da Silva and
             Hil{\'a}rio da Silva, Daniel and Abade, Andr{\'e} and Thomazini, Andr{\'e} and
             Cabral Filho, Fernando Rodrigues and Paim, Tiago do Prado and
             Pinto dos Santos, Erli and Cordeiro, Douglas Farias and
             Alves da Silva, Daiane and Costa, Alan Carlos da},
  title   = {{ChamberFlux}: An open-source web application
             for exploratory analysis and machine learning of soil
             greenhouse gas fluxes measured with the {LI-COR} {LI-7810SC}
             (CH$_4$/CO$_2$/H$_2$O) and {LI-7820} (N$_2$O/H$_2$O) portable
             laser-based trace gas analyzers},
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
