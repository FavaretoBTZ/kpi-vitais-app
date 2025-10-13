import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

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
SCATTER_DEFAULT_X = "RPM - Avg"   # G9 (dispersão) - eixo X
SCATTER_DEFAULT_Y = "pOil - Avg"  # G9 (dispersão) - eixo Y

# ---------- Helpers ----------
def to_datetime_safe(s):
    try:
        return pd.to_datetime(s, errors="coerce")
    except Exception:
        return pd.to_datetime(pd.Series(s), errors="coerce")

@st.cache_data(show_spinner=False)
def load_excel(file):
    df = pd.read_excel(file)

    # Tipos essenciais
    if "SessionDate - Info" in df.columns:
        df["SessionDate - Info"] = to_datetime_safe(df["SessionDate - Info"])
    if "Lap - Info" in df.columns:
        df["Lap - Info"] = pd.to_numeric(df["Lap - Info"], errors="coerce")

    # Eixo X composto
    date_str = df["SessionDate - Info"].dt.strftime("%Y-%m-%d %H:%M").fillna("NA") if "SessionDate - Info" in df.columns else "NA"
    lap_str  = df["Lap - Info"].fillna("").astype(str) if "Lap - Info" in df.columns else "NA"
    sess     = df["SessionName - Info"].astype(str) if "SessionName - Info" in df.columns else "NA"
    df["SessionLapDate"] = sess + " | Lap " + lap_str + " | " + date_str

    # Ordenar
    sort_keys = [c for c in ["SessionDate - Info","SessionName - Info","Lap - Info"] if c in df.columns]
    if sort_keys:
        df = df.sort_values(by=sort_keys, kind="mergesort").reset_index(drop=True)
    return df

def numeric_metric_columns(df):
    cols = []
    for c in df.columns:
        if c in ["SessionLapDate","SessionDate - Info"]:
            continue
        if pd.api.types.is_numeric_dtype(df[c]):
            cols.append(c)
    return cols

def make_line_plot(df_plot, metric, color_by="SessionDate - Info"):
    fig = px.line(
        df_plot, x="SessionLapDate", y=metric,
        color=color_by if color_by in df_plot.columns else None,
        markers=True, labels={"SessionLapDate":"Session | Lap | Date", metric:metric},
        title=None
    )
    fig.update_layout(
        xaxis_tickangle=90, xaxis_title=None, yaxis_title=metric,
        legend_title=(color_by or "Grupo").replace(" - Info",""),
        height=360, margin=dict(l=6, r=6, t=10, b=10)
    )
    return fig

def make_scatter_plot(df_plot, x_metric, y_metric, color_by="SessionDate - Info"):
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
    with c1:
        st.caption("**Mínimo**"); st.markdown(f"**{cmin:.3f}**")
    with c2:
        st.caption("**Máximo**"); st.markdown(f"**{cmax:.3f}**")
    with c3:
        st.caption("**Média**");  st.markdown(f"**{cavg:.3f}**")

# ---------- UI ----------
uploaded = st.file_uploader("Escolha a planilha KPI VITAIS:", type=["xlsx"])
if not uploaded:
    st.info("Envie o arquivo para iniciar a análise.")
    st.stop()

df = load_excel(uploaded)

# ===== Sidebar mínima =====
st.sidebar.header("Filtros")
# CarAlias
car_vals = df["CarAlias - Info"].dropna().unique().tolist() if "CarAlias - Info" in df.columns else []
car_sel  = st.sidebar.selectbox("Selecione o CarAlias:", car_vals) if car_vals else None

# TrackName com opção "Todos"
track_vals = df["TrackName - Info"].dropna().unique().tolist() if "TrackName - Info" in df.columns else []
track_opts = ["Todos"] + track_vals
track_sel  = st.sidebar.selectbox("TrackName - Info:", track_opts)

# ===== Aplica filtros =====
fdf = df.copy()
if car_sel is not None and "CarAlias - Info" in fdf.columns:
    fdf = fdf[fdf["CarAlias - Info"] == car_sel]
if track_sel != "Todos" and "TrackName - Info" in fdf.columns:
    fdf = fdf[fdf["TrackName - Info"] == track_sel]

# Métricas disponíveis e defaults (com fallback)
metric_cols = numeric_metric_columns(fdf)
if not metric_cols:
    st.error("Não encontrei colunas numéricas para plot.")
    st.stop()
line_defaults = [m if m in metric_cols else metric_cols[0] for m in DEFAULT_LINE_METRICS]
scatter_x = SCATTER_DEFAULT_X if SCATTER_DEFAULT_X in metric_cols else metric_cols[0]
scatter_y = SCATTER_DEFAULT_Y if SCATTER_DEFAULT_Y in metric_cols else metric_cols[0]

st.subheader("Painel de 9 Gráficos (3 × 3)")

# -------- Linha 1 --------
c1, c2, c3 = st.columns(3)
with c1:
    st.selectbox("Selecione a métrica (Y Axis):", metric_cols, index=metric_cols.index(line_defaults[0]), key="g1_sel", disabled=False)
    st.plotly_chart(make_line_plot(fdf, st.session_state["g1_sel"]), use_container_width=True)
    render_stats(fdf, st.session_state["g1_sel"])
with c2:
    st.selectbox("Selecione a métrica (Y Axis):", metric_cols, index=metric_cols.index(line_defaults[1]), key="g2_sel", disabled=False)
    st.plotly_chart(make_line_plot(fdf, st.session_state["g2_sel"]), use_container_width=True)
    render_stats(fdf, st.session_state["g2_sel"])
with c3:
    st.selectbox("Selecione a métrica (Y Axis):", metric_cols, index=metric_cols.index(line_defaults[2]), key="g3_sel", disabled=False)
    st.plotly_chart(make_line_plot(fdf, st.session_state["g3_sel"]), use_container_width=True)
    render_stats(fdf, st.session_state["g3_sel"])

st.divider()

# -------- Linha 2 --------
c4, c5, c6 = st.columns(3)
with c4:
    st.selectbox("Selecione a métrica (Y Axis):", metric_cols, index=metric_cols.index(line_defaults[3]), key="g4_sel")
    st.plotly_chart(make_line_plot(fdf, st.session_state["g4_sel"]), use_container_width=True)
    render_stats(fdf, st.session_state["g4_sel"])
with c5:
    st.selectbox("Selecione a métrica (Y Axis):", metric_cols, index=metric_cols.index(line_defaults[4]), key="g5_sel")
    st.plotly_chart(make_line_plot(fdf, st.session_state["g5_sel"]), use_container_width=True)
    render_stats(fdf, st.session_state["g5_sel"])
with c6:
    st.selectbox("Selecione a métrica (Y Axis):", metric_cols, index=metric_cols.index(line_defaults[5]), key="g6_sel")
    st.plotly_chart(make_line_plot(fdf, st.session_state["g6_sel"]), use_container_width=True)
    render_stats(fdf, st.session_state["g6_sel"])

st.divider()

# -------- Linha 3 --------
c7, c8, c9 = st.columns(3)
with c7:
    st.selectbox("Selecione a métrica (Y Axis):", metric_cols, index=metric_cols.index(line_defaults[6]), key="g7_sel")
    st.plotly_chart(make_line_plot(fdf, st.session_state["g7_sel"]), use_container_width=True)
    render_stats(fdf, st.session_state["g7_sel"])
with c8:
    st.selectbox("Selecione a métrica (Y Axis):", metric_cols, index=metric_cols.index(line_defaults[7]), key="g8_sel")
    st.plotly_chart(make_line_plot(fdf, st.session_state["g8_sel"]), use_container_width=True)
    render_stats(fdf, st.session_state["g8_sel"])
with c9:
    # Dispersão (X e Y travados por padrão, mas ainda editáveis se quiser)
    ix = metric_cols.index(scatter_x)
    iy = metric_cols.index(scatter_y)
    cx, cy = st.columns(2)
    with cx:
        st.selectbox("Métrica eixo X:", metric_cols, index=ix, key="g9_x")
    with cy:
        st.selectbox("Métrica eixo Y:", metric_cols, index=iy, key="g9_y")
    st.plotly_chart(make_scatter_plot(fdf, st.session_state["g9_x"], st.session_state["g9_y"]), use_container_width=True)
