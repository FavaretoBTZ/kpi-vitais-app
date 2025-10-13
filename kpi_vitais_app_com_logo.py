import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import re

st.set_page_config(layout="wide")
st.title("KPI VITAIS - Painel 3×3")

# ---------- Defaults pedidos ----------
DEFAULT_LINE_METRICS = [
    "pOil - Min",   # G1
    "pOil - Max",   # G2
    "tWater - Max", # G3
    "pFuel - Min",  # G4
    "pFuel - Max",  # G5
    "VBatt - Min",  # G6
    "tOilGbx - Max",# G7
    "RPM - Max",    # G8
]
SCATTER_DEFAULT_X = "RPM - Avg"   # G9 (dispersão)
SCATTER_DEFAULT_Y = "pOil - Avg"

# ---------- Helpers ----------
def to_datetime_safe(s):
    try:
        return pd.to_datetime(s, errors="coerce")
    except Exception:
        return pd.to_datetime(pd.Series(s), errors="coerce")

@st.cache_data(show_spinner=False)
def load_excel(file):
    df = pd.read_excel(file)

    if "SessionDate - Info" in df.columns:
        df["SessionDate - Info"] = to_datetime_safe(df["SessionDate - Info"])
    if "Lap - Info" in df.columns:
        df["Lap - Info"] = pd.to_numeric(df["Lap - Info"], errors="coerce")

    date_str = df["SessionDate - Info"].dt.strftime("%Y-%m-%d %H:%M").fillna("NA") if "SessionDate - Info" in df.columns else "NA"
    lap_str  = df["Lap - Info"].fillna("").astype(str) if "Lap - Info" in df.columns else "NA"
    sess     = df["SessionName - Info"].astype(str) if "SessionName - Info" in df.columns else "NA"
    df["SessionLapDate"] = sess + " | Lap " + lap_str + " | " + date_str

    sort_keys = [c for c in ["SessionDate - Info","SessionName - Info","Lap - Info"] if c in df.columns]
    if sort_keys:
        df = df.sort_values(by=sort_keys, kind="mergesort").reset_index(drop=True)
    return df

EXCLUDE_SUFFIX = re.compile(r"\s-\s?(info|change)$", re.IGNORECASE)

def numeric_metric_columns(df):
    """
    Retorna colunas 'numéricas por conteúdo':
    - exclui auxiliares (*- Info, *- Change)
    - aceita colunas 'object' que se tornam numéricas com to_numeric
    - exige pelo menos 1 valor não-NaN após coerção
    """
    cols = []
    for c in df.columns:
        if c in ["SessionLapDate","SessionDate - Info","Lap - Info"]:
            continue
        if EXCLUDE_SUFFIX.search(c):
            continue
        ser = pd.to_numeric(df[c], errors="coerce")
        if ser.notna().any():
            cols.append(c)
    return cols

def coerce_numeric_for(df, cols):
    """Converte in-place somente as colunas escolhidas para numérico (sem quebrar outras)."""
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

def init_defaults_in_state(metric_cols):
    # defaults linhas (G1..G8)
    for i, name in enumerate(DEFAULT_LINE_METRICS, start=1):
        key = f"g{i}_sel"
        st.session_state.setdefault(key, name if name in metric_cols else metric_cols[0])
        # Se por algum motivo o valor atual não está mais disponível (após filtro), força fallback
        if st.session_state[key] not in metric_cols:
            st.session_state[key] = metric_cols[0]
    # dispersão
    st.session_state.setdefault("g9_x", SCATTER_DEFAULT_X if SCATTER_DEFAULT_X in metric_cols else metric_cols[0])
    st.session_state.setdefault("g9_y", SCATTER_DEFAULT_Y if SCATTER_DEFAULT_Y in metric_cols else metric_cols[0])
    if st.session_state["g9_x"] not in metric_cols: st.session_state["g9_x"] = metric_cols[0]
    if st.session_state["g9_y"] not in metric_cols: st.session_state["g9_y"] = metric_cols[0]

def make_line_plot(df_plot, metric, color_by="SessionDate - Info"):
    coerce_numeric_for(df_plot, [metric])
    fig = px.line(
        df_plot, x="SessionLapDate", y=metric,
        color=color_by if color_by in df_plot.columns else None,
        markers=True,
        labels={"SessionLapDate":"Session | Lap | Date", metric:metric},
        title=None
    )
    fig.update_layout(
        xaxis_tickangle=90, xaxis_title=None, yaxis_title=metric,
        legend_title=(color_by or "Grupo").replace(" - Info",""),
        height=360, margin=dict(l=6, r=6, t=10, b=10)
    )
    return fig

def make_scatter_plot(df_plot, x_metric, y_metric, color_by="SessionDate - Info"):
    coerce_numeric_for(df_plot, [x_metric, y_metric])
    fig = px.scatter(
        df_plot, x=x_metric, y=y_metric,
        color=color_by if color_by in df_plot.columns else None,
        labels={x_metric:x_metric, y_metric:y_metric}, title=None
    )
    fig.update_layout(
        xaxis_title=x_metric, yaxis_title=y_metric,
        legend_title=(color_by or "Grupo").replace(" - Info",""),
        height=360, margin=dict(l=6, r=6, t=10, b=10)
    )
    fig.update_traces(mode="markers")
    return fig

def render_stats(df_plot, col_name):
    vals = pd.to_numeric(df_plot[col_name], errors="coerce")
    cmin, cmax, cavg = np.nanmin(vals), np.nanmax(vals), np.nanmean(vals)
    c1, c2, c3 = st.columns(3)
    with c1: st.caption("**Mínimo**"); st.markdown(f"**{cmin:.3f}**")
    with c2: st.caption("**Máximo**"); st.markdown(f"**{cmax:.3f}**")
    with c3: st.caption("**Média**");  st.markdown(f"**{cavg:.3f}**")

# ---------- UI ----------
uploaded = st.file_uploader("Escolha a planilha KPI VITAIS:", type=["xlsx"])
if not uploaded:
    st.info("Envie o arquivo para iniciar a análise.")
    st.stop()

df = load_excel(uploaded)

# Sidebar mínima
st.sidebar.header("Filtros")
car_vals = df["CarAlias - Info"].dropna().unique().tolist() if "CarAlias - Info" in df.columns else []
car_sel  = st.sidebar.selectbox("Selecione o CarAlias:", car_vals) if car_vals else None
track_vals = df["TrackName - Info"].dropna().unique().tolist() if "TrackName - Info" in df.columns else []
track_opts = ["Todos"] + track_vals
track_sel  = st.sidebar.selectbox("TrackName - Info:", track_opts)

# Aplica filtros
fdf = df.copy()
if car_sel is not None and "CarAlias - Info" in fdf.columns:
    fdf = fdf[fdf["CarAlias - Info"] == car_sel]
if track_sel != "Todos" and "TrackName - Info" in fdf.columns:
    fdf = fdf[fdf["TrackName - Info"] == track_sel]

# Métricas disponíveis + defaults
metric_cols = numeric_metric_columns(fdf)
if not metric_cols:
    st.error("Não encontrei colunas numéricas úteis para plot.")
    st.stop()

init_defaults_in_state(metric_cols)

st.subheader("Painel de 9 Gráficos (3 × 3)")

# -------- Linha 1 --------
c1, c2, c3 = st.columns(3)
with c1:
    st.session_state["g1_sel"] = st.selectbox("Selecione a métrica (Y Axis):", metric_cols,
                                              index=metric_cols.index(st.session_state["g1_sel"]), key="g1_sel")
    st.plotly_chart(make_line_plot(fdf, st.session_state["g1_sel"]), use_container_width=True)
    render_stats(fdf, st.session_state["g1_sel"])
with c2:
    st.session_state["g2_sel"] = st.selectbox("Selecione a métrica (Y Axis):", metric_cols,
                                              index=metric_cols.index(st.session_state["g2_sel"]), key="g2_sel")
    st.plotly_chart(make_line_plot(fdf, st.session_state["g2_sel"]), use_container_width=True)
    render_stats(fdf, st.session_state["g2_sel"])
with c3:
    st.session_state["g3_sel"] = st.selectbox("Selecione a métrica (Y Axis):", metric_cols,
                                              index=metric_cols.index(st.session_state["g3_sel"]), key="g3_sel")
    st.plotly_chart(make_line_plot(fdf, st.session_state["g3_sel"]), use_container_width=True)
    render_stats(fdf, st.session_state["g3_sel"])

st.divider()

# -------- Linha 2 --------
c4, c5, c6 = st.columns(3)
with c4:
    st.session_state["g4_sel"] = st.selectbox("Selecione a métrica (Y Axis):", metric_cols,
                                              index=metric_cols.index(st.session_state["g4_sel"]), key="g4_sel")
    st.plotly_chart(make_line_plot(fdf, st.session_state["g4_sel"]), use_container_width=True)
    render_stats(fdf, st.session_state["g4_sel"])
with c5:
    st.session_state["g5_sel"] = st.selectbox("Selecione a métrica (Y Axis):", metric_cols,
                                              index=metric_cols.index(st.session_state["g5_sel"]), key="g5_sel")
    st.plotly_chart(make_line_plot(fdf, st.session_state["g5_sel"]), use_container_width=True)
    render_stats(fdf, st.session_state["g5_sel"])
with c6:
    st.session_state["g6_sel"] = st.selectbox("Selecione a métrica (Y Axis):", metric_cols,
                                              index=metric_cols.index(st.session_state["g6_sel"]), key="g6_sel")
    st.plotly_chart(make_line_plot(fdf, st.session_state["g6_sel"]), use_container_width=True)
    render_stats(fdf, st.session_state["g6_sel"])

st.divider()

# -------- Linha 3 --------
c7, c8, c9 = st.columns(3)
with c7:
    st.session_state["g7_sel"] = st.selectbox("Selecione a métrica (Y Axis):", metric_cols,
                                              index=metric_cols.index(st.session_state["g7_sel"]), key="g7_sel")
    st.plotly_chart(make_line_plot(fdf, st.session_state["g7_sel"]), use_container_width=True)
    render_stats(fdf, st.session_state["g7_sel"])
with c8:
    st.session_state["g8_sel"] = st.selectbox("Selecione a métrica (Y Axis):", metric_cols,
                                              index=metric_cols.index(st.session_state["g8_sel"]), key="g8_sel")
    st.plotly_chart(make_line_plot(fdf, st.session_state["g8_sel"]), use_container_width=True)
    render_stats(fdf, st.session_state["g8_sel"])
with c9:
    # Dispersão com defaults
    left, right = st.columns(2)
    with left:
        st.session_state["g9_x"] = st.selectbox("Métrica eixo X:", metric_cols,
                                                index=metric_cols.index(st.session_state["g9_x"]), key="g9_x")
    with right:
        st.session_state["g9_y"] = st.selectbox("Métrica eixo Y:", metric_cols,
                                                index=metric_cols.index(st.session_state["g9_y"]), key="g9_y")
    st.plotly_chart(make_scatter_plot(fdf, st.session_state["g9_x"], st.session_state["g9_y"]), use_container_width=True)
