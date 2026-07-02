"""Dashboard HQVS — Streamlit — 100% Python"""
from __future__ import annotations
from pathlib import Path

import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# ── Config ─────────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "data"

FUNCTIONS: dict[str, tuple[str, str, str]] = {
    "habiter":          ("Habiter",          "🏠", "#2563eb"),
    "travailler":       ("Travailler",        "💼", "#7c3aed"),
    "s_approvisionner": ("S'approvisionner",  "🛒", "#059669"),
    "etre_en_forme":    ("Être en forme",     "🏥", "#ef4444"),
    "apprendre":        ("Apprendre",         "📚", "#f59e0b"),
    "s_epanouir":       ("S'épanouir",        "🎭", "#db2777"),
}

LEVELS: dict[str, str] = {
    "all":           "Tous les niveaux",
    "proximite":     "Local / Proximité",
    "intermediaire": "Intermédiaire",
    "centralite":    "Centralité",
    "prioritaire":   "Prioritaire",
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.block-container { padding-top: 1rem !important; max-width: 1300px; }

/* ── Header ── */
.hqvs-header {
    background: linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 50%, #0ea5e9 100%);
    border-radius: 16px; padding: 22px 28px; margin-bottom: 18px;
}
.hqvs-header h1 { margin: 0; font-size: 1.75rem; font-weight: 800; color: white; letter-spacing: -0.01em; }
.hqvs-header p  { margin: 5px 0 0; font-size: 0.85rem; color: rgba(255,255,255,0.8); }

/* ── KPI cards ── */
.kpi-grid { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 18px; }
.kpi-card {
    flex: 1; min-width: 150px;
    background: white; border-radius: 14px;
    padding: 16px 18px; border: 1px solid #e2e8f0;
    position: relative; overflow: hidden;
}
.kpi-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px;
    border-radius: 14px 14px 0 0;
}
.kpi-card.blue::before   { background: #2563eb; }
.kpi-card.sky::before    { background: #0ea5e9; }
.kpi-card.purple::before { background: #7c3aed; }
.kpi-card.green::before  { background: #059669; }
.kpi-card.orange::before { background: #f59e0b; }
.kpi-card .kpi-label {
    font-size: 0.70rem; font-weight: 700; color: #94a3b8;
    text-transform: uppercase; letter-spacing: 0.07em; margin: 0 0 4px;
}
.kpi-card .kpi-value {
    font-size: 2rem; font-weight: 800; line-height: 1; margin: 0 0 3px;
}
.kpi-card.blue .kpi-value   { color: #1d4ed8; }
.kpi-card.sky .kpi-value    { color: #0284c7; }
.kpi-card.purple .kpi-value { color: #6d28d9; }
.kpi-card.green .kpi-value  { color: #047857; }
.kpi-card.orange .kpi-value { color: #d97706; }
.kpi-card .kpi-sub { font-size: 0.75rem; color: #94a3b8; margin: 0; }
.kpi-card .kpi-icon {
    position: absolute; right: 14px; top: 14px;
    font-size: 1.6rem; opacity: 0.12;
}

/* ── Score badge ── */
.score-badge {
    display: inline-block; padding: 2px 10px; border-radius: 20px;
    font-size: 0.75rem; font-weight: 700; color: white; margin-top: 4px;
}

/* ── Section card ── */
.section-card {
    background: white; border-radius: 12px; padding: 16px 18px;
    border: 1px solid #e2e8f0; margin-bottom: 14px;
}

/* ── Function chip ── */
.func-chip {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 8px 14px; border-radius: 10px; margin: 4px;
    font-size: 0.85rem; font-weight: 600;
}

/* ── Info / Warning boxes ── */
.info-box {
    background: #eff6ff; border-left: 4px solid #2563eb;
    border-radius: 0 8px 8px 0; padding: 12px 16px; font-size: 0.87rem; color: #1e3a8a;
    margin: 8px 0;
}
.warn-box {
    background: #fffbeb; border-left: 4px solid #f59e0b;
    border-radius: 0 8px 8px 0; padding: 12px 16px; font-size: 0.87rem; color: #78350f;
    margin: 8px 0;
}
</style>
"""

# ── Chargement des données ──────────────────────────────────────────────────────
def _fix(v: object) -> object:
    if not isinstance(v, str):
        return v
    try:
        return v.encode("latin1").decode("utf-8")
    except Exception:
        return v

def _norm_bool(s: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(s):
        return s.fillna(False)
    if pd.api.types.is_numeric_dtype(s):
        return s.fillna(0).astype(bool)
    return s.astype(str).str.strip().str.lower().isin({"true", "1", "yes", "oui"})

@st.cache_data(show_spinner="Chargement des isochrones…")
def load_gdf() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(DATA_DIR / "isochrones_walking_15min.geojson")
    for col in gdf.select_dtypes("object").columns:
        gdf[col] = gdf[col].map(_fix)
    for col in [*FUNCTIONS, "proximite", "intermediaire", "centralite", "prioritaire"]:
        if col in gdf.columns:
            gdf[col] = _norm_bool(gdf[col])
    gdf = gdf.to_crs("EPSG:4326") if gdf.crs else gdf.set_crs("EPSG:4326")
    gdf["lon"] = gdf.geometry.centroid.x
    gdf["lat"]  = gdf.geometry.centroid.y
    gdf["nb_fonctions"] = sum(gdf[c].astype(int) for c in FUNCTIONS if c in gdf.columns)
    return gdf

@st.cache_data(show_spinner="Chargement de la classification BPE…")
def load_classif() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "bpe24key_classification.csv", sep=";", encoding="utf-8")
    df.columns = df.columns.str.strip()
    for col in df.select_dtypes("object").columns:
        df[col] = df[col].astype(str).str.strip().map(_fix)
    return df.drop_duplicates(subset=["typequ"], keep="first")

# ── Helpers ────────────────────────────────────────────────────────────────────
def apply_filters(gdf: gpd.GeoDataFrame, function: str, level: str, priority: bool) -> gpd.GeoDataFrame:
    out = gdf
    if function != "all" and function in out.columns:
        out = out[out[function].astype(bool)]
    if level != "all" and level in out.columns:
        out = out[out[level].astype(bool)]
    if priority and "prioritaire" in out.columns:
        out = out[out["prioritaire"].astype(bool)]
    return out

def compute_score(df: gpd.GeoDataFrame) -> float:
    """Score proxy : moyenne arithmétique des taux de couverture × 10"""
    r = [float(df[c].mean()) for c in FUNCTIONS if c in df.columns and len(df) > 0]
    return round(min(10, max(0, sum(r) / len(r) * 10)), 1) if r else 0.0

def compute_weighted_score(df: gpd.GeoDataFrame) -> float:
    """Score pondéré (méthode Monterey) : moyenne géométrique des taux de couverture.
    Pénalise les fonctions absentes bien plus que la moyenne arithmétique."""
    import math
    if len(df) == 0:
        return 0.0
    rates = [float(df[c].mean()) for c in FUNCTIONS if c in df.columns]
    if not rates:
        return 0.0
    product = math.prod(r + 0.001 for r in rates)
    geomean = product ** (1 / len(rates))
    return round(min(10, geomean * 10), 1)

def adapt_od_gdf(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Convertit le format OD (nb_habiter, nb_travailler…) en format dashboard (booléens 0/1).
    Une ligne = un bâtiment. habiter=1 si au moins un équipement "habiter" est accessible.
    Mappe aussi les niveaux : nb_prox_* → proximite, nb_inter_* → intermediaire, etc.
    """
    out = gdf.copy()
    func_keys = list(FUNCTIONS.keys())

    for k in func_keys:
        nb_col = f"nb_{k}"
        if nb_col in gdf.columns:
            out[k] = (gdf[nb_col] > 0).astype(float)
        else:
            out[k] = 0.0

    # Niveaux de proximité : True si au moins une fonction a des équipements à ce niveau
    prox_cols  = [f"nb_prox_{k}"  for k in func_keys if f"nb_prox_{k}"  in gdf.columns]
    inter_cols = [f"nb_inter_{k}" for k in func_keys if f"nb_inter_{k}" in gdf.columns]
    centr_cols = [f"nb_centr_{k}" for k in func_keys if f"nb_centr_{k}" in gdf.columns]

    out["proximite"]     = (gdf[prox_cols].sum(axis=1)  > 0).astype(float) if prox_cols  else 0.0
    out["intermediaire"] = (gdf[inter_cols].sum(axis=1) > 0).astype(float) if inter_cols else 0.0
    out["centralite"]    = (gdf[centr_cols].sum(axis=1) > 0).astype(float) if centr_cols else 0.0
    out["prioritaire"]   = (gdf["nb_total_prioritaire"]  > 0).astype(float) \
                           if "nb_total_prioritaire" in gdf.columns else 0.0

    # Colonnes utiles pour la carte — centroïde direct en WGS84 (pas de reprojection)
    geom_wgs = out.geometry if (out.crs and out.crs.to_epsg() == 4326) \
               else out.set_crs("EPSG:4326", allow_override=True).geometry
    out["lat"] = geom_wgs.centroid.y
    out["lon"] = geom_wgs.centroid.x
    if "nom" not in out.columns:
        out["nom"] = out["batiment_id"].astype(str) if "batiment_id" in out.columns \
                     else pd.RangeIndex(len(out)).astype(str)

    return out

def approx_isochrones(gdf: gpd.GeoDataFrame, mode: str) -> gpd.GeoDataFrame:
    """
    Approxime les isochrones vélo/voiture par buffer circulaire en mètres (EPSG:2154).
    Vitesses : marche 5 km/h → 1 250 m · vélo 15 km/h → 3 750 m · voiture 40 km/h → 10 000 m
    Note : les attributs (fonctions sociales) restent ceux de la marche — seule la géométrie change.
    Pour des scores différents par mode, importez des GeoJSON routés réels.
    """
    radius_m = {"walking": 1_250, "cycling": 3_750, "car": 10_000}
    r = radius_m.get(mode, 1_250)

    projected = gdf.to_crs("EPSG:2154")
    buffered  = projected.copy()
    buffered.geometry = projected.geometry.centroid.buffer(r)
    return buffered.to_crs("EPSG:4326")

def score_color(s: float) -> str:
    if s < 3:  return "#ef4444"
    if s < 5:  return "#f97316"
    if s < 7:  return "#eab308"
    if s < 9:  return "#22c55e"
    return "#15803d"

def score_label(s: float) -> str:
    if s < 3:  return "Faible"
    if s < 5:  return "Moyen-bas"
    if s < 7:  return "Moyen"
    if s < 9:  return "Bon"
    return "Excellent"

def fmt(n: int | float) -> str:
    return f"{n:,}".replace(",", " ")

# ── Composants KPI ────────────────────────────────────────────────────────────
def kpi_card(label: str, value: str, sub: str, color_cls: str, icon: str) -> str:
    return f"""
<div class="kpi-card {color_cls}">
  <span class="kpi-icon">{icon}</span>
  <p class="kpi-label">{label}</p>
  <p class="kpi-value">{value}</p>
  <p class="kpi-sub">{sub}</p>
</div>"""

# ── Graphiques ─────────────────────────────────────────────────────────────────
PLOTLY_LAYOUT = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                     font=dict(family="Inter, sans-serif", color="#334155"))

def fig_map(df: gpd.GeoDataFrame) -> go.Figure:
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnée pour ces filtres", showarrow=False,
                           font=dict(size=14, color="#64748b"))
        return fig

    sample  = df if len(df) <= 2000 else df.sample(2000, random_state=42)
    nom_col = "nom" if "nom" in sample.columns else ("typequ" if "typequ" in sample.columns else sample.columns[0])
    lib_col = "libelle_typequ" if "libelle_typequ" in sample.columns else nom_col

    # Données OD (vélo/voiture) : chaque ligne est un bâtiment, pas un équipement.
    # On détermine la fonction dominante (nb_xxx le plus élevé) pour colorier sans superposition.
    _func_keys = [k for k in FUNCTIONS if k in sample.columns]
    _all_covered = len(_func_keys) > 0 and all(
        sample[k].astype(bool).all() for k in _func_keys
    )

    fig = go.Figure()
    if _all_covered and "batiment_id" in sample.columns:
        # Mode OD : colorie chaque bâtiment par sa fonction la plus accessible
        nb_cols = {k: f"nb_{k}" for k in _func_keys if f"nb_{k}" in sample.columns}
        if nb_cols:
            dominant = sample[[f"nb_{k}" for k in nb_cols]].idxmax(axis=1) \
                               .str.replace("nb_", "", regex=False)
        else:
            dominant = pd.Series(_func_keys[0], index=sample.index)
        for key, (label, icon, color) in FUNCTIONS.items():
            if key not in _func_keys:
                continue
            sub = sample[dominant == key]
            if sub.empty:
                continue
            fig.add_trace(go.Scattermapbox(
                lat=sub["lat"], lon=sub["lon"],
                mode="markers",
                name=f"{icon} {label}",
                marker=dict(size=6, color=color, opacity=0.7),
                text=sub[nom_col].fillna(""),
                customdata=list(zip(sub[lib_col].fillna(""), sub.index.astype(str))),
                hovertemplate=(
                    f"<b>Bâtiment %{{text}}</b>"
                    f"<br>Fonction dominante : {icon} {label}"
                    f"<extra></extra>"
                ),
            ))
    else:
        # Mode marche (isochrones) : un tracé par fonction
        for key, (label, icon, color) in FUNCTIONS.items():
            if key not in sample.columns:
                continue
            sub = sample[sample[key].astype(bool)]
            if sub.empty:
                continue
            fig.add_trace(go.Scattermapbox(
                lat=sub["lat"], lon=sub["lon"],
                mode="markers",
                name=f"{icon} {label}",
                marker=dict(size=8, color=color, opacity=0.82),
                text=sub[nom_col].fillna(""),
                customdata=list(zip(sub[lib_col].fillna(""), sub.index.astype(str))),
                hovertemplate=(
                    f"<b>%{{text}}</b><br>%{{customdata[0]}}"
                    f"<br><span style='color:{color}'>■</span> {label}"
                    f"<br><i style='color:#94a3b8'>Cliquez pour voir les équipements à 15 min</i><extra></extra>"
                ),
            ))

    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=float(sample["lat"].mean()), lon=float(sample["lon"].mean())),
            zoom=11,
        ),
        height=430,
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(
            orientation="v",
            x=0.01, y=0.99,
            bgcolor="rgba(255,255,255,0.88)",
            bordercolor="#e2e8f0",
            borderwidth=1,
            font=dict(size=11),
        ),
        uirevision="map",
    )
    return fig

def fig_radar(df: gpd.GeoDataFrame) -> go.Figure:
    keys   = [k for k in FUNCTIONS if k in df.columns]
    labels = [f"{FUNCTIONS[k][1]} {FUNCTIONS[k][0]}" for k in keys]
    values = [round(float(df[k].mean()) * 10, 1) if len(df) > 0 else 0.0 for k in keys]
    lc = labels + [labels[0]]
    vc = values + [values[0]]
    fig = go.Figure()
    # Zone remplie
    fig.add_trace(go.Scatterpolar(
        r=vc, theta=lc, fill="toself",
        fillcolor="rgba(37,99,235,0.15)",
        line=dict(color="#2563eb", width=2.5),
        name="Score /10",
        mode="lines",
    ))
    # Points avec valeurs affichées
    fig.add_trace(go.Scatterpolar(
        r=values, theta=labels, mode="markers+text",
        text=[f"<b>{v}</b>" for v in values],
        textposition="top center",
        textfont=dict(size=12, color="#1e293b"),
        marker=dict(size=12, color=[FUNCTIONS[k][2] for k in keys],
                    line=dict(color="white", width=2)),
        name="Valeurs",
        showlegend=False,
    ))
    fig.update_layout(
        height=400,
        margin=dict(l=70, r=70, t=40, b=40),
        polar=dict(
            radialaxis=dict(
                visible=True, range=[0, 10],
                tickvals=[2, 4, 6, 8, 10],
                ticktext=["2", "4", "6", "8", "10"],
                tickfont=dict(size=10, color="#64748b"),
                gridcolor="#e2e8f0",
                linecolor="#e2e8f0",
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color="#1e293b", family="Inter, sans-serif"),
                gridcolor="#e2e8f0",
                linecolor="#e2e8f0",
            ),
            bgcolor="rgba(248,250,252,0.8)",
        ),
        legend=dict(orientation="h", y=-0.12, font=dict(size=11)),
        **PLOTLY_LAYOUT,
    )
    return fig

def fig_bar_levels(df: gpd.GeoDataFrame) -> go.Figure:
    keys   = ["proximite", "intermediaire", "centralite", "prioritaire"]
    labels = ["Proximité", "Intermédiaire", "Centralité", "Prioritaire"]
    colors = ["#2563eb", "#7c3aed", "#059669", "#ef4444"]
    values = [int(df[k].sum()) if k in df.columns else 0 for k in keys]
    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h", marker_color=colors,
        text=values, textposition="outside",
        hovertemplate="%{y}: %{x}<extra></extra>",
    ))
    fig.update_layout(height=210, xaxis_title="Isochrones", **PLOTLY_LAYOUT)
    return fig

def fig_bar_functions(df: gpd.GeoDataFrame) -> go.Figure:
    keys   = [k for k in FUNCTIONS if k in df.columns]
    labels = [FUNCTIONS[k][0] for k in keys]
    values = [int(df[k].sum()) if len(df) > 0 else 0 for k in keys]
    colors = [FUNCTIONS[k][2] for k in keys]
    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker=dict(color=colors, line=dict(color="white", width=1)),
        text=values, textposition="outside",
        hovertemplate="%{y} : %{x} isochrones<extra></extra>",
    ))
    fig.update_layout(height=290, xaxis_title="Isochrones",
                      yaxis=dict(autorange="reversed"), **PLOTLY_LAYOUT)
    return fig

def fig_top_types(df: gpd.GeoDataFrame) -> go.Figure:
    col = "libelle_typequ" if "libelle_typequ" in df.columns \
          else ("typequ" if "typequ" in df.columns else None)
    if col is None:
        fig = go.Figure()
        fig.add_annotation(text="Données OD — pas de type d'équipement par bâtiment",
                           showarrow=False, font=dict(size=13, color="#64748b"))
        fig.update_layout(height=200, **PLOTLY_LAYOUT)
        return fig
    top = df[col].fillna("Non renseigné").value_counts().head(20)
    colors = px.colors.sequential.Blues_r[:len(top)]
    fig = go.Figure(go.Bar(
        x=top.values, y=top.index, orientation="h",
        marker_color=colors,
        hovertemplate="%{y}: %{x}<extra></extra>",
    ))
    fig.update_layout(height=500, xaxis_title="Isochrones",
                      yaxis=dict(autorange="reversed"), **PLOTLY_LAYOUT)
    return fig

def fig_gauge(rate: float) -> go.Figure:
    color = score_color(rate / 10)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=rate,
        number={"suffix": "%", "font": {"size": 44, "color": color}},
        title={"text": "Taux de couverture BPE", "font": {"size": 14, "color": "#64748b"}},
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor="#e2e8f0"),
            bar=dict(color=color, thickness=0.28),
            bgcolor="white",
            bordercolor="#e2e8f0",
            steps=[
                {"range": [0,  50], "color": "#fef2f2"},
                {"range": [50, 80], "color": "#fffbeb"},
                {"range": [80,100], "color": "#f0fdf4"},
            ],
            threshold=dict(line=dict(color="#15803d", width=4), thickness=0.75, value=90),
        ),
    ))
    fig.update_layout(height=260, **PLOTLY_LAYOUT)
    return fig

def fig_pie_functions(df: gpd.GeoDataFrame) -> go.Figure:
    keys   = [k for k in FUNCTIONS if k in df.columns]
    labels = [f"{FUNCTIONS[k][1]} {FUNCTIONS[k][0]}" for k in keys]
    values = [int(df[k].sum()) if len(df) > 0 else 0 for k in keys]
    colors = [FUNCTIONS[k][2] for k in keys]
    fig = go.Figure(go.Pie(
        labels=labels, values=values, marker_colors=colors,
        hole=0.42, textinfo="label+percent",
        hovertemplate="%{label}: %{value}<extra></extra>",
    ))
    fig.update_layout(height=300, showlegend=False, **PLOTLY_LAYOUT)
    return fig

def fig_score_comparison(score_proxy: float, score_pondere: float) -> go.Figure:
    """Graphique comparant score proxy (arithmétique) vs score pondéré (géométrique)."""
    categories = ["Score proxy\n(arithmétique)", "Score pondéré\n(géométrique)"]
    values     = [score_proxy, score_pondere]
    colors     = [score_color(score_proxy), score_color(score_pondere)]
    fig = go.Figure()
    for cat, val, col in zip(categories, values, colors):
        fig.add_trace(go.Bar(
            x=[cat], y=[val],
            marker_color=col,
            text=[f"<b>{val}/10</b>"],
            textposition="outside",
            width=0.35,
            showlegend=False,
            hovertemplate=f"{cat} : {val}/10<extra></extra>",
        ))
    fig.add_hline(y=score_proxy, line_dash="dot", line_color="#94a3b8", line_width=1)
    fig.update_layout(
        height=280,
        yaxis=dict(range=[0, 12], title="Score /10"),
        margin=dict(l=10, r=10, t=20, b=10),
        barmode="group",
        **PLOTLY_LAYOUT,
    )
    return fig

def fig_radar_comparison(df: gpd.GeoDataFrame) -> go.Figure:
    """Radar superposant score arithmétique vs géométrique par fonction."""
    import math
    keys   = [k for k in FUNCTIONS if k in df.columns]
    labels = [FUNCTIONS[k][0] for k in keys]
    arith  = [round(float(df[k].mean()) * 10, 1) if len(df) > 0 else 0 for k in keys]
    geom   = [round(min(10, (float(df[k].mean()) + 0.001) ** (1 / len(keys)) * 10), 1)
              for k in keys]
    lc = labels + [labels[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=arith + [arith[0]], theta=lc,
        fill="toself", fillcolor="rgba(37,99,235,0.10)",
        line=dict(color="#2563eb", width=2), name="Proxy (arithmétique)"))
    fig.add_trace(go.Scatterpolar(r=geom + [geom[0]], theta=lc,
        fill="toself", fillcolor="rgba(219,39,119,0.10)",
        line=dict(color="#db2777", width=2, dash="dash"), name="Pondéré (géométrique)"))
    fig.update_layout(
        height=320,
        margin=dict(l=55, r=55, t=30, b=20),
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 10], tickfont=dict(size=9), gridcolor="#e2e8f0"),
            angularaxis=dict(tickfont=dict(size=10), gridcolor="#e2e8f0"),
        ),
        legend=dict(orientation="h", y=-0.15, font=dict(size=10)),
        **PLOTLY_LAYOUT,
    )
    return fig

# ── Graphiques Qualité ─────────────────────────────────────────────────────────

def fig_coverage_donut(matched: int, total: int) -> go.Figure:
    unmatched = total - matched
    fig = go.Figure(go.Pie(
        labels=["Classés ✅", "Non classés ⚠️"],
        values=[matched, unmatched],
        marker_colors=["#22c55e", "#f97316"],
        hole=0.55,
        textinfo="percent",
        hovertemplate="%{label}: %{value} isochrones<extra></extra>",
    ))
    fig.add_annotation(
        text=f"<b>{matched/total*100:.0f}%</b>" if total > 0 else "—",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=22, color="#1e293b"),
    )
    fig.update_layout(
        height=260,
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", y=-0.08, font=dict(size=11)),
        **PLOTLY_LAYOUT,
    )
    return fig

def fig_coverage_by_function(df: gpd.GeoDataFrame, class_types: set) -> go.Figure:
    is_matched = df["typequ"].astype(str).isin(class_types) \
                 if "typequ" in df.columns else pd.Series(False, index=df.index)
    labels, rates, totals, colors = [], [], [], []
    for key, (label, icon, color) in FUNCTIONS.items():
        if key not in df.columns:
            continue
        sub = df[df[key].astype(bool)]
        if sub.empty:
            continue
        rate = is_matched[sub.index].mean() * 100 if len(sub) > 0 else 0
        labels.append(f"{icon} {label}")
        rates.append(round(rate, 1))
        totals.append(len(sub))
        colors.append(color)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=rates, y=labels, orientation="h",
        marker=dict(
            color=rates,
            colorscale=[[0, "#ef4444"], [0.5, "#eab308"], [1, "#22c55e"]],
            cmin=0, cmax=100,
            line=dict(color="white", width=1),
        ),
        text=[f"{r:.0f}% ({t})" for r, t in zip(rates, totals)],
        textposition="outside",
        hovertemplate="%{y} : %{x:.1f}% classés<extra></extra>",
    ))
    fig.add_vline(x=80, line_dash="dash", line_color="#94a3b8",
                  annotation_text="Seuil 80%", annotation_position="top right",
                  annotation_font=dict(size=10, color="#94a3b8"))
    fig.update_layout(
        height=300,
        xaxis=dict(range=[0, 115], title="% d'isochrones classés"),
        yaxis=dict(autorange="reversed"),
        margin=dict(l=10, r=60, t=20, b=10),
        **PLOTLY_LAYOUT,
    )
    return fig

def fig_coverage_by_level(df: gpd.GeoDataFrame, class_types: set) -> go.Figure:
    is_matched = df["typequ"].astype(str).isin(class_types) \
                 if "typequ" in df.columns else pd.Series(False, index=df.index)
    level_keys   = ["proximite", "intermediaire", "centralite", "prioritaire"]
    level_labels = ["Proximité", "Intermédiaire", "Centralité", "Prioritaire"]
    level_colors = ["#2563eb", "#7c3aed", "#059669", "#ef4444"]
    rates, counts = [], []
    for key in level_keys:
        if key not in df.columns:
            rates.append(0); counts.append(0)
            continue
        sub = df[df[key].astype(bool)]
        rate = is_matched[sub.index].mean() * 100 if len(sub) > 0 else 0
        rates.append(round(rate, 1))
        counts.append(len(sub))

    fig = go.Figure(go.Bar(
        x=level_labels, y=rates,
        marker_color=level_colors,
        text=[f"{r:.0f}%<br>({c})" for r, c in zip(rates, counts)],
        textposition="outside",
        hovertemplate="%{x} : %{y:.1f}% classés<extra></extra>",
    ))
    fig.add_hline(y=80, line_dash="dash", line_color="#94a3b8",
                  annotation_text="Seuil 80%", annotation_position="top right",
                  annotation_font=dict(size=10, color="#94a3b8"))
    fig.update_layout(
        height=300,
        yaxis=dict(range=[0, 120], title="% classés"),
        margin=dict(l=10, r=20, t=20, b=10),
        **PLOTLY_LAYOUT,
    )
    return fig

def fig_missing_types_bar(df: gpd.GeoDataFrame, class_types: set) -> go.Figure:
    unmatched = df[~df["typequ"].astype(str).isin(class_types)]
    if unmatched.empty:
        fig = go.Figure()
        fig.add_annotation(text="✅ Aucun type manquant", showarrow=False,
                           font=dict(size=14, color="#22c55e"))
        return fig
    lib_col = "libelle_typequ" if "libelle_typequ" in unmatched.columns else "typequ"
    top = unmatched[lib_col].fillna(unmatched["typequ"]).value_counts().head(15)
    fig = go.Figure(go.Bar(
        x=top.values, y=top.index, orientation="h",
        marker=dict(color="#f97316", line=dict(color="white", width=1)),
        text=top.values, textposition="outside",
        hovertemplate="%{y}: %{x} isochrones non classés<extra></extra>",
    ))
    fig.update_layout(
        height=380,
        xaxis_title="Isochrones non classés",
        yaxis=dict(autorange="reversed"),
        margin=dict(l=10, r=40, t=10, b=10),
        **PLOTLY_LAYOUT,
    )
    return fig

@st.cache_data
def _load_od_mode(mode: str) -> gpd.GeoDataFrame | None:
    """Charge et adapte les isochrones OD vélo/voiture si le fichier existe."""
    fname = {"cycling": "isochrones_cycling_15min.geojson",
             "car":     "isochrones_car_15min.geojson"}.get(mode)
    path = DATA_DIR / fname if fname else None
    if path and path.exists():
        return adapt_od_gdf(gpd.read_file(path))
    return None

@st.cache_data
def load_filosofi() -> gpd.GeoDataFrame | None:
    path = DATA_DIR / "filosofi_200m.geojson"
    if path.exists():
        return gpd.read_file(path)
    return None

@st.cache_data
def load_grille_50m() -> gpd.GeoDataFrame | None:
    path = DATA_DIR / "grille_50m.geojson"
    if path.exists():
        return gpd.read_file(path)
    return None

# ── Application ────────────────────────────────────────────────────────────────
def main() -> None:
    st.set_page_config(page_title="Dashboard HQVS", page_icon="🏙️",
                       layout="wide", initial_sidebar_state="expanded")
    st.markdown(CSS, unsafe_allow_html=True)

    # Vérification des fichiers
    missing = [f for f in ["isochrones_walking_15min.geojson", "bpe24key_classification.csv"]
               if not (DATA_DIR / f).exists()]
    if missing:
        st.error(f"Fichiers manquants dans `data/` : {', '.join(missing)}")
        st.stop()

    gdf         = load_gdf()
    classif     = load_classif()
    gdf_cycling = _load_od_mode("cycling")
    gdf_car     = _load_od_mode("car")
    gdf_pop     = load_filosofi()
    gdf_grid    = load_grille_50m()

    # ── Sidebar ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### 🏙️ HQVS Dashboard")
        st.caption("Sorbonne × Chaire ETI · BPE 2024")
        st.divider()

        st.markdown("**Mode de transport**")
        transport = st.radio(
            "Transport",
            ["🚶 Marche (15 min)", "🚴 Vélo (15 min)", "🚗 Voiture (15 min)"],
            label_visibility="collapsed",
            key="transport_mode",
        )
        transport_mode_key = {
            "🚶 Marche (15 min)": "walking",
            "🚴 Vélo (15 min)":   "cycling",
            "🚗 Voiture (15 min)": "car",
        }[transport]
        is_approx = transport_mode_key != "walking"
        if is_approx:
            has_real = (transport_mode_key == "cycling" and gdf_cycling is not None) or \
                       (transport_mode_key == "car"     and gdf_car     is not None)
            if has_real:
                st.markdown(
                    '<div style="background:#f0fdf4;border-left:3px solid #22c55e;'
                    'padding:8px 10px;border-radius:0 6px 6px 0;font-size:0.8rem;color:#166534">'
                    '✅ <strong>Données réelles chargées</strong><br>'
                    'Isochrones routés Valhalla (Sorbonne × Chaire ETI).'
                    '</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div style="background:#fffbeb;border-left:3px solid #f59e0b;'
                    'padding:8px 10px;border-radius:0 6px 6px 0;font-size:0.8rem;color:#78350f">'
                    '📐 <strong>Approximation géométrique</strong><br>'
                    'Buffer circulaire (vélo ×3 · voiture ×8 vs marche).'
                    '</div>',
                    unsafe_allow_html=True,
                )

        st.divider()
        st.markdown("**Fonction sociale**")
        selected_func = st.selectbox(
            "Fonction",
            ["all", *FUNCTIONS],
            format_func=lambda k: "Toutes les fonctions" if k == "all"
                                  else f"{FUNCTIONS[k][1]} {FUNCTIONS[k][0]}",
            label_visibility="collapsed",
        )

        st.markdown("**Niveau de proximité**")
        selected_level = st.selectbox(
            "Niveau", list(LEVELS),
            format_func=lambda k: LEVELS[k],
            label_visibility="collapsed",
        )

        priority_only = st.toggle("Prioritaires uniquement", value=False)
        st.divider()
        max_pts = st.slider("Points affichés sur la carte", 200, 3000, 1500, step=100)

    # ── Données filtrées (multi-modal : réel > importé > approximation) ───────
    if transport_mode_key == "walking":
        base_gdf = gdf
    elif transport_mode_key == "cycling":
        sess = st.session_state.get("gdf_cycling")
        if sess is not None:
            base_gdf = sess
        elif gdf_cycling is not None:
            base_gdf = gdf_cycling
        else:
            base_gdf = approx_isochrones(gdf, "cycling")
    else:  # car
        sess = st.session_state.get("gdf_car")
        if sess is not None:
            base_gdf = sess
        elif gdf_car is not None:
            base_gdf = gdf_car
        else:
            base_gdf = approx_isochrones(gdf, "car")
    filtered        = apply_filters(base_gdf, selected_func, selected_level, priority_only)
    score           = compute_score(filtered)
    score_pondere   = compute_weighted_score(filtered)
    slbl            = score_label(score)
    scol            = score_color(score)
    nb_iso          = len(filtered)
    nb_equip        = filtered["equipement_id"].nunique() if "equipement_id" in filtered.columns else "—"
    nb_types        = filtered["typequ"].nunique() if "typequ" in filtered.columns else "—"
    nb_fonc         = sum(1 for c in FUNCTIONS if c in filtered.columns and filtered[c].any())

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="hqvs-header">'
        '<h1>🏙️ Dashboard HQVS</h1>'
        '<p>Haute Qualité de Vie Sociétale · Proximité urbaine · Sorbonne × Chaire ETI · BPE 2024</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── KPIs ─────────────────────────────────────────────────────────────────
    score_badge  = f'<span class="score-badge" style="background:{scol}">{slbl}</span>'
    scol_p       = score_color(score_pondere)
    delta_str    = f"{'▲' if score_pondere > score else '▼'} {abs(score_pondere - score):.1f} vs proxy"
    st.markdown(
        '<div class="kpi-grid">'
        + kpi_card("Score proxy (marche)", f"{score}<small style='font-size:1rem'>/10</small>",
                   score_badge, "blue", "📊")
        + kpi_card("Score pondéré ⭐", f"{score_pondere}<small style='font-size:1rem'>/10</small>",
                   f'<span class="score-badge" style="background:{scol_p}">{delta_str}</span>',
                   "purple", "🏆")
        + kpi_card("Secteurs étudiés", fmt(nb_iso), "zones de marche 15 min", "sky", "📍")
        + kpi_card("Équipements à proximité", fmt(nb_equip) if isinstance(nb_equip, int) else nb_equip,
                   "services uniques recensés", "green", "🏛️")
        + kpi_card("Besoins couverts", f"{nb_fonc}<small style='font-size:1rem'>/6</small>",
                   "sur 6 fonctions sociales", "orange", "🔢")
        + '</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "⭐ Score pondéré = moyenne géométrique (méthode Monterey) · pénalise davantage les fonctions absentes. "
        "Les deux scores seront pondérés par population quand le fichier Filosofi sera disponible."
    )

    # ── Pages (onglets) ───────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📍 Vue principale",
        "📊 Analyse des fonctions",
        "🏆 Score pondéré",
        "🚴 Modes de transport",
        "👥 Population",
        "🗺️ Grille 50 m",
        "🔎 Qualité des données",
        "📖 Documentation",
    ])

    # ── Page 1 : Vue principale ───────────────────────────────────────────────
    with tab1:
        col_left, col_right = st.columns([1.3, 1])

        with col_left:
            _mode_label = {"walking": "Marche 15 min", "cycling": "Vélo 15 min", "car": "Voiture 15 min"}[transport_mode_key]
            st.subheader(f"🗺️ Carte interactive · {_mode_label}")
            map_df = filtered if len(filtered) <= max_pts else filtered.sample(max_pts, random_state=42)
            click_event = st.plotly_chart(
                fig_map(map_df),
                use_container_width=True,
                on_select="rerun",
                selection_mode="points",
                key="main_map",
            )
            legend_items = " · ".join(
                f'<span style="color:{c}">■</span> {icon} {lbl}'
                for k, (lbl, icon, c) in FUNCTIONS.items()
            )
            st.markdown(
                f'<p style="font-size:0.72rem;color:#64748b;margin-top:4px">{legend_items}</p>',
                unsafe_allow_html=True,
            )

            # ── Résultats du clic ────────────────────────────────────────────
            pts = (click_event.selection.points
                   if click_event and click_event.selection else [])
            if pts:
                raw_idx = pts[0].get("customdata", [None, None])
                try:
                    row_idx = int(raw_idx[1])
                    clicked = gdf.loc[row_idx]
                    nom_clicked = clicked["nom"] if "nom" in gdf.columns and pd.notna(clicked["nom"]) else clicked.get("typequ", "Équipement")
                    lib_clicked = clicked["libelle_typequ"] if "libelle_typequ" in gdf.columns else ""
                    polygon = clicked.geometry

                    # Tous les équipements dont le centroïde est dans l'isochrone
                    nearby = gdf[gdf.geometry.centroid.within(polygon)].copy()
                    nearby = nearby[nearby.index != row_idx]  # exclure le point cliqué lui-même

                    # Fonctions couvertes par l'équipement cliqué
                    foncs_clicked = [
                        f"{FUNCTIONS[k][1]} {FUNCTIONS[k][0]}"
                        for k in FUNCTIONS if k in gdf.columns and bool(clicked[k])
                    ]

                    st.markdown(
                        f'<div class="section-card" style="border-left:4px solid #2563eb;margin-top:12px">'
                        f'<strong>📍 {nom_clicked}</strong>'
                        + (f'<br><span style="color:#64748b;font-size:0.85rem">{lib_clicked}</span>' if lib_clicked else "")
                        + (f'<br><span style="font-size:0.82rem">{" · ".join(foncs_clicked)}</span>' if foncs_clicked else "")
                        + f'</div>',
                        unsafe_allow_html=True,
                    )

                    st.markdown(f"**{len(nearby)} équipement(s) accessibles à 15 min à pied**")

                    if nearby.empty:
                        st.info("Aucun autre équipement dans cette zone de 15 min.")
                    else:
                        # Regrouper par fonction
                        for key, (label, icon, color) in FUNCTIONS.items():
                            if key not in nearby.columns:
                                continue
                            grp = nearby[nearby[key].astype(bool)]
                            if grp.empty:
                                continue
                            nom_col_n = "nom" if "nom" in grp.columns else "typequ"
                            lib_col_n = "libelle_typequ" if "libelle_typequ" in grp.columns else nom_col_n
                            noms = grp[nom_col_n].fillna("").tolist()
                            libs = grp[lib_col_n].fillna("").tolist()
                            rows = "".join(
                                f'<li><span style="font-weight:600">{n}</span>'
                                + (f' <span style="color:#94a3b8;font-size:0.8rem">— {l}</span>' if l and l != n else "")
                                + "</li>"
                                for n, l in zip(noms, libs)
                            )
                            st.markdown(
                                f'<div style="margin-bottom:8px">'
                                f'<div style="color:{color};font-weight:700;font-size:0.85rem;margin-bottom:4px">'
                                f'{icon} {label} ({len(grp)})</div>'
                                f'<ul style="margin:0;padding-left:18px;font-size:0.83rem;color:#334155">{rows}</ul>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                except (IndexError, KeyError, ValueError, TypeError):
                    st.info("Cliquez sur un point pour voir les équipements à 15 min.")

        with col_right:
            st.subheader("🕸️ Radar HQVS")
            st.plotly_chart(fig_radar(filtered), use_container_width=True)

            st.subheader("Répartition par niveau")
            st.plotly_chart(fig_bar_levels(filtered), use_container_width=True)

        with st.expander("Voir les données détaillées"):
            show_cols = ["nom", "typequ", "libelle_typequ",
                         "proximite", "intermediaire", "centralite",
                         *FUNCTIONS]
            show_cols = [c for c in show_cols if c in filtered.columns]
            st.dataframe(
                filtered[show_cols].drop(columns="geometry", errors="ignore"),
                use_container_width=True, hide_index=True,
            )
            st.download_button(
                "⬇️ Exporter CSV",
                data=filtered.drop(columns="geometry", errors="ignore").to_csv(index=False).encode("utf-8"),
                file_name="hqvs_filtrees.csv", mime="text/csv",
            )

    # ── Page 2 : Analyse des fonctions ───────────────────────────────────────
    with tab2:
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("Isochrones par fonction sociale")
            st.plotly_chart(fig_bar_functions(filtered), use_container_width=True)

            st.subheader("Répartition en camembert")
            st.plotly_chart(fig_pie_functions(filtered), use_container_width=True)

        with col_b:
            st.subheader("Top 20 types d'équipements")
            st.plotly_chart(fig_top_types(filtered), use_container_width=True)

    # ── Page 3 : Score pondéré ───────────────────────────────────────────────
    with tab3:
        st.subheader("🏆 Score pondéré — Méthode Monterey")
        st.markdown(
            '<div class="info-box">'
            '<strong>Méthode Monterey (Université de Monterrey)</strong> : '
            'la moyenne <em>géométrique</em> pénalise bien plus fortement une fonction absente '
            'que la moyenne arithmétique. Un quartier excellent sur 5 fonctions mais sans accès '
            'à l\'emploi aura un score bien plus bas avec cette méthode.'
            '</div>',
            unsafe_allow_html=True,
        )
        col_cmp, col_radar = st.columns(2)
        with col_cmp:
            st.subheader("Comparaison des deux scores")
            st.plotly_chart(fig_score_comparison(score, score_pondere), use_container_width=True)
            diff = score - score_pondere
            if diff > 0.5:
                st.markdown(
                    f'<div class="warn-box">⚠️ Le score pondéré est <strong>{diff:.1f} points plus bas</strong> '
                    f'que le proxy. Certaines fonctions sociales sont peu ou pas couvertes — '
                    f'elles pénalisent le score géométrique.</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div class="info-box">✅ Les deux scores sont proches : '
                    'la couverture est relativement équilibrée entre les 6 fonctions.</div>',
                    unsafe_allow_html=True,
                )
        with col_radar:
            st.subheader("Radar comparatif")
            st.plotly_chart(fig_radar_comparison(filtered), use_container_width=True)

        st.divider()
        st.subheader("Détail par fonction")
        import math
        rows = []
        for k, (label, icon, color) in FUNCTIONS.items():
            if k not in filtered.columns: continue
            taux  = float(filtered[k].mean()) * 100 if len(filtered) > 0 else 0
            arith = round(taux / 10, 1)
            geom  = round(min(10, (taux / 100 + 0.001) * 10), 1)
            rows.append({"Fonction": f"{icon} {label}", "Taux couverture": f"{taux:.1f}%",
                         "Score proxy": arith, "Score pondéré": geom,
                         "Écart": round(arith - geom, 1)})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # ── Page 4 : Modes de transport ──────────────────────────────────────────
    with tab4:
        st.subheader("🚴 Modes de transport — Comparaison automatique")
        st.markdown(
            '<div class="info-box">'
            '📐 <strong>Approximation automatique activée</strong> : les zones vélo et voiture '
            'sont estimées par buffer circulaire à partir des centroïdes marche '
            '(vélo = rayon ×3 · voiture = rayon ×8). '
            'Pour des isochrones routés réels, importez un GeoJSON ci-dessous — '
            'il remplacera automatiquement l\'approximation.'
            '</div>',
            unsafe_allow_html=True,
        )

        # Priorité : session_state (importé manuellement) > données réelles (_load_od_mode) > approximation
        def _best_gdf(mode_key, fallback_real):
            sess = st.session_state.get(f"gdf_{mode_key}")
            if sess is not None:     return sess, "✅ Fichier importé"
            if fallback_real is not None: return fallback_real, "✅ Données Sorbonne"
            return approx_isochrones(gdf, mode_key), "📐 Approximation géométrique"

        gdf_walking = gdf
        _gdf_cyc, _lbl_cyc = _best_gdf("cycling", gdf_cycling)
        _gdf_car, _lbl_car  = _best_gdf("car",     gdf_car)

        modes_info = [
            ("🚶 Marche 15 min", gdf_walking, "#22c55e", "walking", "✅ Données réelles BPE"),
            ("🚴 Vélo 15 min",   _gdf_cyc,   "#f59e0b", "cycling", _lbl_cyc),
            ("🚗 Voiture 15 min", _gdf_car,  "#ef4444", "car",     _lbl_car),
        ]

        # Graphique de comparaison (toujours visible)
        scores_modes  = [compute_score(apply_filters(d, selected_func, selected_level, priority_only))
                         for _, d, _, _, _ in modes_info]
        colors_modes  = [c for _, _, c, _, _ in modes_info]
        labels_modes  = [l for l, _, _, _, _ in modes_info]

        fig_cmp = go.Figure(go.Bar(
            x=labels_modes, y=scores_modes,
            marker_color=colors_modes,
            text=[f"<b>{s}/10</b>" for s in scores_modes],
            textposition="outside",
            width=0.5,
        ))
        fig_cmp.update_layout(
            height=320,
            yaxis=dict(range=[0, 13], title="Score HQVS /10"),
            margin=dict(l=10, r=10, t=20, b=10),
            **PLOTLY_LAYOUT,
        )
        st.subheader("Scores HQVS par mode de transport")
        st.plotly_chart(fig_cmp, use_container_width=True)

        st.caption(
            "📐 = estimation géométrique · ✅ = données routées réelles. "
            "Sélectionnez le mode actif dans la barre latérale pour explorer la carte."
        )

        st.markdown(
            '<div class="warn-box" style="margin-top:8px">'
            '⚠️ <strong>Limitation de l\'approximation</strong> : en mode approximé, '
            'les <em>scores HQVS restent identiques</em> à la marche car les attributs '
            '(fonctions sociales couvertes) viennent de la classification BPE — '
            'ils ne changent pas quand on élargit la zone géographique. '
            'Seule la <strong>forme des polygones sur la carte</strong> change visuellement. '
            '<br><br>'
            '✅ <strong>Pour de vrais scores différents par mode</strong> : importez les '
            'GeoJSON issus du repo Sorbonne (<code>access_od_cycling_15min</code>, '
            '<code>access_od_driving_car_15min</code>) via les boutons ci-dessous.'
            '</div>',
            unsafe_allow_html=True,
        )
        st.divider()

        # Statut + upload pour vélo et voiture
        st.subheader("Améliorer la précision avec vos propres données")
        c_walk, c_bike, c_car = st.columns(3)
        with c_walk:
            st.markdown(
                '<div class="section-card" style="border-left:4px solid #22c55e;text-align:center">'
                '<p style="font-size:2rem">🚶</p>'
                '<strong style="color:#15803d">Marche 15 min</strong><br><br>'
                '<span style="background:#dcfce7;color:#15803d;padding:3px 10px;'
                'border-radius:20px;font-size:0.8rem">✅ Données réelles BPE 2024</span>'
                '</div>',
                unsafe_allow_html=True,
            )
        with c_bike:
            velo_status = "✅ Fichier importé" if "gdf_cycling" in st.session_state else "📐 Approximation active"
            velo_color  = "#15803d" if "gdf_cycling" in st.session_state else "#d97706"
            velo_bg     = "#dcfce7" if "gdf_cycling" in st.session_state else "#fef9c3"
            st.markdown(
                f'<div class="section-card" style="border-left:4px solid #f59e0b;text-align:center">'
                f'<p style="font-size:2rem">🚴</p>'
                f'<strong style="color:#d97706">Vélo 15 min</strong><br><br>'
                f'<span style="background:{velo_bg};color:{velo_color};padding:3px 10px;'
                f'border-radius:20px;font-size:0.8rem">{velo_status}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            velo_file = st.file_uploader("Remplacer par un GeoJSON réel (vélo)",
                                         type=["geojson", "json"], key="upload_velo_tab")
            if velo_file:
                try:
                    st.session_state["gdf_cycling"] = gpd.read_file(velo_file)
                    st.success(f"✅ {len(st.session_state['gdf_cycling'])} isochrones vélo chargés — rechargez la page.")
                except Exception as e:
                    st.error(f"Erreur : {e}")
        with c_car:
            car_status = "✅ Fichier importé" if "gdf_car" in st.session_state else "📐 Approximation active"
            car_color  = "#15803d" if "gdf_car" in st.session_state else "#dc2626"
            car_bg     = "#dcfce7" if "gdf_car" in st.session_state else "#fee2e2"
            st.markdown(
                f'<div class="section-card" style="border-left:4px solid #ef4444;text-align:center">'
                f'<p style="font-size:2rem">🚗</p>'
                f'<strong style="color:#dc2626">Voiture 15 min</strong><br><br>'
                f'<span style="background:{car_bg};color:{car_color};padding:3px 10px;'
                f'border-radius:20px;font-size:0.8rem">{car_status}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            car_file = st.file_uploader("Remplacer par un GeoJSON réel (voiture)",
                                        type=["geojson", "json"], key="upload_car_tab")
            if car_file:
                try:
                    st.session_state["gdf_car"] = gpd.read_file(car_file)
                    st.success(f"✅ {len(st.session_state['gdf_car'])} isochrones voiture chargés — rechargez la page.")
                except Exception as e:
                    st.error(f"Erreur : {e}")

    # ── Page 5 : Population ──────────────────────────────────────────────────
    with tab5:
        st.subheader("👥 Population — Filosofi INSEE 200 m")
        if gdf_pop is None:
            st.warning("Fichier `data/filosofi_200m.geojson` introuvable.")
        else:
            pop_total   = gdf_pop["ind"].sum()
            men_total   = gdf_pop["men"].sum()
            men_pauv    = gdf_pop["men_pauv"].sum()
            taux_pauv   = men_pauv / men_total * 100 if men_total > 0 else 0
            seniors     = gdf_pop["ind_65_79"].sum() + gdf_pop["ind_80p"].sum()
            jeunes      = gdf_pop["ind_0_3"].sum() + gdf_pop["ind_4_5"].sum() \
                        + gdf_pop["ind_6_10"].sum() + gdf_pop["ind_11_17"].sum()

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Population totale", fmt(int(pop_total)), "habitants · Sète")
            k2.metric("Ménages", fmt(int(men_total)), "unités Filosofi")
            k3.metric("Taux de pauvreté", f"{taux_pauv:.1f}%", "ménages pauvres")
            k4.metric("65 ans et +", fmt(int(seniors)), f"{seniors/pop_total*100:.1f}% de la pop.")

            st.divider()
            col_map, col_charts = st.columns([1.4, 1])
            with col_map:
                st.subheader("Carte de densité de population")
                centroids = gdf_pop.to_crs("EPSG:2154").geometry.centroid.to_crs("EPSG:4326")
                fig_pop_map = go.Figure(go.Scattermapbox(
                    lat=centroids.y, lon=centroids.x,
                    mode="markers",
                    marker=dict(
                        size=gdf_pop["ind"].clip(0, 500).fillna(0) / 30 + 4,
                        color=gdf_pop["ind"],
                        colorscale="YlOrRd",
                        cmin=0, cmax=float(gdf_pop["ind"].quantile(0.95)),
                        showscale=True,
                        colorbar=dict(title="Habitants", thickness=12, len=0.6),
                        opacity=0.8,
                    ),
                    text=gdf_pop["ind"].apply(lambda x: f"{x:.0f} hab."),
                    hovertemplate="<b>%{text}</b><br>lat %{lat:.3f} lon %{lon:.3f}<extra></extra>",
                ))
                fig_pop_map.update_layout(
                    mapbox=dict(style="carto-positron",
                                center=dict(lat=centroids.y.mean(), lon=centroids.x.mean()),
                                zoom=12),
                    height=420, margin=dict(l=0, r=0, t=0, b=0),
                    **PLOTLY_LAYOUT,
                )
                st.plotly_chart(fig_pop_map, use_container_width=True)

            with col_charts:
                st.subheader("Pyramide des âges")
                age_bins = {
                    "0–3 ans":   gdf_pop["ind_0_3"].sum(),
                    "4–5 ans":   gdf_pop["ind_4_5"].sum(),
                    "6–10 ans":  gdf_pop["ind_6_10"].sum(),
                    "11–17 ans": gdf_pop["ind_11_17"].sum(),
                    "18–24 ans": gdf_pop["ind_18_24"].sum(),
                    "25–39 ans": gdf_pop["ind_25_39"].sum(),
                    "40–54 ans": gdf_pop["ind_40_54"].sum(),
                    "55–64 ans": gdf_pop["ind_55_64"].sum(),
                    "65–79 ans": gdf_pop["ind_65_79"].sum(),
                    "80 ans +":  gdf_pop["ind_80p"].sum(),
                }
                fig_age = go.Figure(go.Bar(
                    x=list(age_bins.values()), y=list(age_bins.keys()),
                    orientation="h",
                    marker_color="#2563eb",
                    text=[f"{v:.0f}" for v in age_bins.values()],
                    textposition="outside",
                ))
                fig_age.update_layout(height=380, margin=dict(l=10,r=40,t=10,b=10),
                                      xaxis_title="Individus", **PLOTLY_LAYOUT)
                st.plotly_chart(fig_age, use_container_width=True)

                st.subheader("Types de logements")
                log_data = {
                    "Avant 1945":  gdf_pop["log_av45"].sum(),
                    "1945–1970":   gdf_pop["log_45_70"].sum(),
                    "1970–1990":   gdf_pop["log_70_90"].sum(),
                    "Après 1990":  gdf_pop["log_ap90"].sum(),
                }
                fig_log = go.Figure(go.Pie(
                    labels=list(log_data.keys()),
                    values=list(log_data.values()),
                    hole=0.45,
                    marker_colors=["#ef4444","#f59e0b","#22c55e","#2563eb"],
                ))
                fig_log.update_layout(height=240, margin=dict(l=10,r=10,t=10,b=10),
                                      **PLOTLY_LAYOUT)
                st.plotly_chart(fig_log, use_container_width=True)

    # ── Page 6 : Grille 50 m ─────────────────────────────────────────────────
    with tab6:
        st.subheader("🗺️ Grille 50 m — Diagnostic spatial fin")
        st.markdown(
            '<div class="info-box">'
            '✅ <strong>Données chargées</strong> : grille 50 × 50 m de Sète '
            f'({fmt(len(gdf_grid)) if gdf_grid is not None else "—"} carreaux). '
            'Chaque carreau représente une zone de 2 500 m². La carte ci-dessous '
            'montre la couverture spatiale de la grille sur le territoire.'
            '</div>',
            unsafe_allow_html=True,
        ) if gdf_grid is not None else st.warning("Fichier `data/grille_50m.geojson` introuvable.")

        if gdf_grid is not None:
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.markdown(
                    '<div class="section-card" style="border-left:4px solid #059669">'
                    '<strong>✅ Avantages de la grille 50 m</strong>'
                    '<ul style="font-size:0.87rem;color:#475569;margin-top:6px">'
                    '<li>Résolution très fine (50 × 50 m = 2 500 m²)</li>'
                    '<li>Détecte les zones blanches <em>intra-quartier</em></li>'
                    '<li>Jointure possible avec Filosofi (revenus, pauvreté)</li>'
                    '<li>Idéal pour le diagnostic des inégalités hyper-locales</li>'
                    '</ul>'
                    '</div>',
                    unsafe_allow_html=True,
                )
            with col_g2:
                st.markdown(
                    '<div class="section-card" style="border-left:4px solid #f59e0b">'
                    '<strong>⚠️ Limites</strong>'
                    '<ul style="font-size:0.87rem;color:#475569;margin-top:6px">'
                    '<li>Secret statistique : carrés &lt; 11 habitants masqués</li>'
                    '<li>Moins lisible pour les élus (trop granulaire)</li>'
                    '<li>Carrés sous-peuplés à agréger ou masquer</li>'
                    '<li>Recommandation : basculer vers IRIS pour la présentation politique</li>'
                    '</ul>'
                    '</div>',
                    unsafe_allow_html=True,
                )

            st.subheader("Carte de la grille 50 m")
            try:
                _g = gdf_grid.set_crs("EPSG:4326", allow_override=True)
                _lats = _g.geometry.centroid.y
                _lons = _g.geometry.centroid.x
                _mask = _lats.notna() & _lons.notna() & (_lats != 0)
                _clat = float(_lats[_mask].mean()) if _mask.any() else 43.40
                _clon = float(_lons[_mask].mean()) if _mask.any() else 3.70
                fig_grid_map = go.Figure(go.Scattermapbox(
                    lat=_lats[_mask].tolist(),
                    lon=_lons[_mask].tolist(),
                    mode="markers",
                    marker=dict(size=4, color="#7c3aed", opacity=0.6),
                    hovertemplate="Carreau 50×50 m<extra></extra>",
                    name="Carreaux 50m",
                ))
                fig_grid_map.update_layout(
                    mapbox=dict(style="open-street-map",
                                center=dict(lat=_clat, lon=_clon), zoom=13),
                    height=480, margin=dict(l=0, r=0, t=0, b=0),
                    **PLOTLY_LAYOUT,
                )
                st.plotly_chart(fig_grid_map, use_container_width=True)
                st.caption(f"🗺️ {fmt(_mask.sum())} carreaux 50×50 m · chaque point = centre d'un carreau")
            except Exception as e:
                st.error(f"Erreur carte grille : {e}")

    # ── Page 7 : Qualité des données ─────────────────────────────────────────
    with tab7:
        _has_bpe = "typequ" in filtered.columns
        if not _has_bpe:
            st.info(
                "ℹ️ L'analyse de qualité BPE est disponible uniquement en mode "
                "**🚶 Marche 15 min** (données isochrones avec classification d'équipements). "
                "Repassez en marche dans la barre latérale pour voir cet onglet."
            )
        if _has_bpe:
            class_types = set(classif["typequ"].dropna().astype(str))
            iso_types   = set(filtered["typequ"].dropna().astype(str))
            matched     = int(filtered["typequ"].astype(str).isin(class_types).sum())
            total       = len(filtered)
            rate        = matched / total * 100 if total > 0 else 0.0
            unmatched   = total - matched
            missing_t   = sorted(iso_types - class_types)

            # ── Ligne 1 : KPIs + Jauge + Donut ──────────────────────────────
            st.subheader("Vue d'ensemble")
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Total isochrones", fmt(total))
            k2.metric("Classés ✅", fmt(matched), f"{rate:.1f}%")
            k3.metric("Non classés ⚠️", fmt(unmatched), f"{100 - rate:.1f}%", delta_color="inverse")
            k4.metric("Types manquants", len(missing_t), "codes BPE absents", delta_color="inverse")

            col_jauge, col_donut = st.columns(2)
            with col_jauge:
                st.markdown("**Taux de couverture global**")
                st.plotly_chart(fig_gauge(rate), use_container_width=True)
            with col_donut:
                st.markdown("**Classés vs Non classés**")
                st.plotly_chart(fig_coverage_donut(matched, total), use_container_width=True)

            st.divider()

            # ── Ligne 2 : Couverture par fonction + par niveau ───────────────
            st.subheader("Couverture par catégorie")
            col_fonc, col_niv = st.columns(2)
            with col_fonc:
                st.markdown("**Par fonction sociale** — % d'isochrones dont le type est référencé")
                st.plotly_chart(fig_coverage_by_function(filtered, class_types), use_container_width=True)
            with col_niv:
                st.markdown("**Par niveau de proximité** — % d'isochrones classés pour chaque niveau")
                st.plotly_chart(fig_coverage_by_level(filtered, class_types), use_container_width=True)

            st.divider()

            # ── Ligne 3 : Top types non classés + tableau ───────────────────
            st.subheader("Types d'équipements non classés")
            col_bar, col_tbl = st.columns([1.2, 1])
            with col_bar:
                st.markdown(f"**Top 15 des types non référencés** ({len(missing_t)} types manquants)")
                st.plotly_chart(fig_missing_types_bar(filtered, class_types), use_container_width=True)
            with col_tbl:
                st.markdown("**Détail des types non classés**")
                if missing_t:
                    missing_df = (
                        filtered[~filtered["typequ"].astype(str).isin(class_types)]
                        .groupby("typequ", dropna=False)
                        .agg(isochrones=("typequ", "count"), exemple=("nom", "first"))
                        .reset_index()
                        .sort_values("isochrones", ascending=False)
                        .rename(columns={"typequ": "Code BPE", "isochrones": "Nb isochrones", "exemple": "Exemple"})
                    )
                    st.dataframe(missing_df, use_container_width=True, hide_index=True, height=380)
                else:
                    st.markdown(
                        '<div class="info-box">✅ Tous les types sont référencés dans la classification BPE.</div>',
                        unsafe_allow_html=True,
                    )

    # ── Page 8 : Documentation ────────────────────────────────────────────────
    with tab8:

        # ── Section 1 : Les 6 fonctions (expandable) ─────────────────────────
        st.subheader("Les 6 fonctions sociales HQVS")
        st.caption("Cliquez sur une fonction pour afficher le détail et les équipements associés.")

        FUNC_DETAILS: dict[str, dict] = {
            "habiter": {
                "desc":      "Accès au logement, hébergement d'urgence, services d'aide à domicile.",
                "pourquoi":  "Se loger est le premier besoin fondamental. Sans accès à un logement stable ou à des services d'aide, la qualité de vie chute immédiatement.",
                "exemples":  ["MAIRIE", "Bureau d'aide juridictionnelle", "France Services", "Hébergement d'urgence", "Services à domicile"],
                "indicateur":"% d'isochrones couvrant la fonction « Habiter »",
            },
            "travailler": {
                "desc":      "Accès aux zones d'activité, pôles emploi, espaces de coworking.",
                "pourquoi":  "L'accès à l'emploi et aux ressources professionnelles conditionne l'autonomie économique des habitants.",
                "exemples":  ["France Travail (Pôle emploi)", "Zone d'activité économique", "Espace de coworking", "CFA / centre de formation"],
                "indicateur":"% d'isochrones couvrant la fonction « Travailler »",
            },
            "s_approvisionner": {
                "desc":      "Accès aux commerces alimentaires, marchés, commerces de proximité.",
                "pourquoi":  "Pouvoir faire ses courses à pied est un marqueur fort de l'autonomie quotidienne, surtout pour les personnes sans voiture.",
                "exemples":  ["Supermarché", "Marché local", "Boulangerie", "Bureau de Poste", "Épicerie"],
                "indicateur":"% d'isochrones couvrant la fonction « S'approvisionner »",
            },
            "etre_en_forme": {
                "desc":      "Accès aux équipements sportifs, médicaux, paramédicaux et de bien-être.",
                "pourquoi":  "La santé physique et mentale dépend de l'accès aux soins et aux espaces de pratique sportive.",
                "exemples":  ["Médecin généraliste", "Pharmacie", "Gymnase / salle de sport", "Piscine municipale", "Maison de santé"],
                "indicateur":"% d'isochrones couvrant la fonction « Être en forme »",
            },
            "apprendre": {
                "desc":      "Accès aux établissements scolaires, universités, bibliothèques, formations.",
                "pourquoi":  "L'accès à l'éducation dès le plus jeune âge détermine les trajectoires sociales et professionnelles.",
                "exemples":  ["École primaire", "Collège / Lycée", "Université", "Bibliothèque municipale", "Médiathèque", "Centre de formation"],
                "indicateur":"% d'isochrones couvrant la fonction « Apprendre »",
            },
            "s_epanouir": {
                "desc":      "Accès aux équipements culturels, loisirs, espaces verts et associations.",
                "pourquoi":  "Le bien-être social et la vie culturelle sont des dimensions essentielles de la qualité de vie qui vont au-delà des besoins primaires.",
                "exemples":  ["Théâtre / Cinéma", "Musée", "Parc / Jardin public", "Association sportive", "Centre social", "Maison des jeunes"],
                "indicateur":"% d'isochrones couvrant la fonction « S'épanouir »",
            },
        }

        for k, (label, icon, color) in FUNCTIONS.items():
            detail = FUNC_DETAILS[k]
            nb_iso_fonc = int(filtered[k].sum()) if k in filtered.columns else 0
            pct = round(nb_iso_fonc / len(filtered) * 100, 1) if len(filtered) > 0 else 0
            with st.expander(f"{icon} {label}  —  {nb_iso_fonc:,} isochrones ({pct}%)".replace(",", " ")):
                c_desc, c_stat = st.columns([1.6, 1])
                with c_desc:
                    st.markdown(
                        f'<div style="border-left:4px solid {color};padding:10px 14px;'
                        f'background:#f8fafc;border-radius:0 8px 8px 0;margin-bottom:10px">'
                        f'<p style="margin:0;font-size:0.95rem;color:#1e293b">{detail["desc"]}</p>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"**Pourquoi c'est important ?**")
                    st.markdown(
                        f'<p style="font-size:0.88rem;color:#475569">{detail["pourquoi"]}</p>',
                        unsafe_allow_html=True,
                    )
                    st.markdown("**Exemples d'équipements concernés :**")
                    st.markdown(
                        "".join(
                            f'<span style="display:inline-block;background:{color}18;color:{color};'
                            f'border:1px solid {color}44;border-radius:6px;padding:3px 10px;'
                            f'margin:3px;font-size:0.82rem;font-weight:600">{eq}</span>'
                            for eq in detail["exemples"]
                        ),
                        unsafe_allow_html=True,
                    )
                with c_stat:
                    st.markdown(f"**Indicateur mesuré**")
                    st.markdown(
                        f'<p style="font-size:0.83rem;color:#64748b">{detail["indicateur"]}</p>',
                        unsafe_allow_html=True,
                    )
                    st.metric(label="Isochrones couverts", value=fmt(nb_iso_fonc),
                              delta=f"{pct}% du total")

        st.divider()

        # ── Section 2 : Glossaire ─────────────────────────────────────────────
        st.subheader("📖 Glossaire — les mots techniques expliqués simplement")

        GLOSSAIRE = [
            ("Isochrone",        "🗺️", "#2563eb",
             "Une zone dessinée sur la carte qui représente tout ce qu'on peut atteindre en 15 minutes à pied depuis un équipement. "
             "C'est comme tracer un cercle autour de chez vous, mais en suivant les vrais chemins.",
             "Si vous êtes à la pharmacie, l'isochrone montre tout ce qui est accessible à pied en 15 min autour d'elle."),
            ("HQVS",             "⭐", "#7c3aed",
             "Haute Qualité de Vie Sociétale. C'est un score qui mesure à quel point les habitants d'un territoire ont facilement accès "
             "aux services essentiels du quotidien : se soigner, apprendre, se loger, travailler, faire ses courses et s'épanouir.",
             "Un quartier avec un bon score HQVS est un quartier où tout est accessible sans voiture."),
            ("Fonction sociale",  "🔢", "#059669",
             "Un grand besoin du quotidien regroupant plusieurs services. On en compte 6 dans le modèle HQVS : "
             "Habiter, Travailler, S'approvisionner, Être en forme, Apprendre, S'épanouir.",
             "Aller chez le médecin et faire du sport font partie de la même fonction sociale : « Être en forme »."),
            ("IRIS",             "🏘️", "#ef4444",
             "Découpage géographique créé par l'INSEE pour analyser les statistiques dans les grandes villes. "
             "Un IRIS regroupe environ 2 000 habitants — c'est comme un mini-quartier administratif.",
             "Paris est découpé en ~1 000 IRIS. Chaque IRIS a ses propres statistiques de population et de revenus."),
            ("Carreau 50 m",     "⬛", "#f59e0b",
             "La France est découpée en petits carrés de 50 × 50 mètres. Chaque carré contient des informations "
             "sur la population qui y vit. C'est une analyse très fine, comme zoomer au maximum sur la carte.",
             "Là où un IRIS donne une moyenne sur 2 000 personnes, le carreau 50 m permet de voir les inégalités "
             "à l'intérieur d'un même quartier."),
            ("BPE",              "📋", "#0ea5e9",
             "Base Permanente des Équipements, publiée par l'INSEE chaque année. Elle recense tous les équipements "
             "et services disponibles en France : écoles, médecins, commerces, gymnases, etc.",
             "C'est la source de données qui alimente ce dashboard. Chaque point sur la carte vient de la BPE 2024."),
            ("Choroplèthe",      "🎨", "#db2777",
             "Une carte où les zones sont colorées selon une valeur numérique (un score, un pourcentage…). "
             "Plus la couleur est foncée ou chaude, plus la valeur est élevée.",
             "Une carte choroplèthe du score HQVS colorerait en vert les quartiers bien desservis "
             "et en rouge ceux qui manquent de services."),
        ]

        cols_glos = st.columns(2)
        for i, (terme, icone, color, explication, exemple) in enumerate(GLOSSAIRE):
            with cols_glos[i % 2]:
                with st.expander(f"{icone} **{terme}**"):
                    st.markdown(
                        f'<p style="font-size:0.9rem;color:#1e293b;margin-bottom:10px">{explication}</p>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<div style="background:{color}12;border-left:3px solid {color};'
                        f'border-radius:0 6px 6px 0;padding:8px 12px;font-size:0.83rem;color:#475569">'
                        f'<strong>Exemple :</strong> {exemple}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

        st.divider()

        # ── Section 3 : Méthodologie + Sources + Calendrier ──────────────────
        col_meth, col_src = st.columns(2)

        with col_meth:
            st.subheader("Méthodologie du score")
            st.markdown(
                '<div class="info-box">'
                '<strong>Score HQVS proxy (actuel)</strong><br>'
                'Moyenne des taux de couverture par fonction × 10<br><br>'
                '<em>Exemple : 40 % des isochrones couvrent « Habiter » et 60 % « Être en forme »'
                ' → score = 5,0 / 10</em>'
                '</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="warn-box">'
                '<strong>⚠️ Score final (à venir) :</strong> pondérer par la population via le fichier '
                'IRIS ou carreaux 50 m (Filosofi INSEE).<br>'
                '<code>Score_i = Σ(f_k × w_k) / Σ(w_k)</code>, normalisé 0–10'
                '</div>',
                unsafe_allow_html=True,
            )
            st.subheader("Calendrier")
            st.markdown("""
| Étape | Date |
|---|---|
| Rendu intermédiaire | **3 juillet 2025** |
| Soutenances | 11 septembre 2025 |
| Rendu final | **15 septembre 2025** |
""")

        with col_src:
            st.subheader("Sources des données")
            st.markdown("""
| Fichier | Source | Millésime |
|---|---|---|
| `isochrones_walking_15min.geojson` | Calcul isochrones sur BPE | 2024 |
| `bpe24key_classification.csv` | BPE INSEE + Chaire ETI | 2024 |
""")
            st.subheader("Niveaux de proximité")
            levels_info = [
                ("Local / Proximité",  "Équipements du quotidien accessibles à pied en moins de 15 min. Ex : boulangerie, médecin, école primaire."),
                ("Intermédiaire",      "Équipements de quartier accessibles en moins de 30 min. Ex : collège, supermarché, pharmacie."),
                ("Centralité",         "Équipements rares et spécialisés, niveau ville ou agglomération. Ex : hôpital, université, tribunal."),
                ("Prioritaire",        "Équipements identifiés comme prioritaires pour la politique publique locale."),
            ]
            for lvl, desc in levels_info:
                st.markdown(
                    f'<div class="section-card" style="margin-bottom:8px;padding:10px 14px">'
                    f'<strong>{lvl}</strong>'
                    f'<p style="margin:3px 0 0;font-size:0.83rem;color:#64748b">{desc}</p>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

if __name__ == "__main__":
    main()
