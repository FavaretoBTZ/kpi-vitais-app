import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
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

def make_line_plot(df_plot, metric, color_by):
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

def make_scatter_plot(df_plot, x_metric, y_metric, color_by):
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

def render_card_line(df_plot, metric_options, default_metric_name, key_suffix, color_by, show_stats=True):
    # seletor individual (default travado para a métrica pedida)
    idx = metric_options.index(default_metric_name) if default_metric_name in metric_options else 0
    metric = st.selectbox("Selecione a métrica (Y Axis):", metric_options, index=idx, key=f"metric_{key_suffix}")
    st.plotly_chart(make_line_plot(df_plot, metric, color_by), use_container_width=True)

    if show_stats:
        vals = pd.to_numeric(df_plot[metric], errors="coerce")
        cmin, cmax, cavg = np.nanmin(vals), np.nanmax(vals), np.nanmean(vals)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.caption("**Mínimo**"); st.markdown(f"**{cmin:.3f}**")
        with c2:
            st.caption("**Máximo**"); st.markdown(f"**{cmax:.3f}**")
        with c3:
            st.caption("**Média**");  st.markdown(f"**{cavg:.3f}**")

def render_card_scatter(df_plot, metric_options, default_x, default_y, key_suffix, color_by):
    ix = metric_options.index(default_x) if default_x in metric_options else 0
    iy = metric_options.index(default_y) if default_y in metric_options else 0
    colx, coly = st.columns(2)
    with colx:
        x_metric = st.selectbox("Métrica eixo X:", metric_options, index=ix, key=f"scatter_x_{key_suffix}")
    with coly:
        y_metric = st.selectbox("Métrica eixo Y:", metric_options, index=iy, key=f"scatter_y_{key_suffix}")
    st.plotly_chart(make_scatter_plot(df_plot, x_metric, y_metric, color_by), use_container_width=True)

def export_pdf(filtered_df, metrics, group_col, car_alias):
    buf = BytesIO()
    with PdfPages(buf) as pdf:
        for metric in metrics:
            plt.figure(figsize=(14,7))
            if group_col in filtered_df.columns:
                groups = filtered_df.groupby(group_col, dropna=False)
            else:
                groups = [("All", filtered_df)]
            for name, group in (groups if hasattr(groups,"groups") else groups):
                y = pd.to_numeric(group[metric], errors="coerce")
                x = group["SessionLapDate"].astype(str)
                plt.plot(x, y, marker="o", label=str(name))
            plt.title(f"{metric} por Session/Lap/Date")
            plt.xlabel("Session | Lap | Date"); plt.ylabel(metric)
            plt.xticks(rotation=90); plt.grid(axis="y")
            plt.legend(title=(group_col or "Grupo").replace(" - Info",""))
            plt.gca().xaxis.set_major_locator(MaxNLocator(18))
            plt.tight_layout(); pdf.savefig(); plt.close()
    buf.seek(0)
    return buf, f"{car_alias or 'AllCars'}_KPIs.pdf"

# ---------- UI ----------
uploaded = st.file_uploader("Escolha a planilha KPI VITAIS:", type=["xlsx"])
if not uploaded:
    st.info("Envie o arquivo para iniciar a análise.")
    st.stop()

df = load_excel(uploaded)

# Filtros globais
st.sidebar.header("Filtros")
car_vals = df["CarAlias - Info"].dropna().unique().tolist() if "CarAlias - Info" in df.columns else []
car_sel  = st.sidebar.selectbox("Selecione o CarAlias:", car_vals) if car_vals else None

sess_vals = df["SessionName - Info"].dropna().unique().tolist() if "SessionName - Info" in df.columns else []
sess_sel  = st.sidebar.multiselect("Filtrar por SessionName (opcional):", sess_vals, default=sess_vals)

drv_vals = df["DriverName - Info"].dropna().unique().tolist() if "DriverName - Info" in df.columns else []
drv_sel  = st.sidebar.multiselect("Filtrar por Driver (opcional):", drv_vals, default=drv_vals)

color_options = [c for c in ["SessionDate - Info","SessionName - Info","DriverName - Info"] if c in df.columns]
color_by = st.sidebar.selectbox("Agrupar por (legenda) nos gráficos:", color_options) if color_options else None

# Aplica filtros
fdf = df.copy()
if car_sel is not None and "CarAlias - Info" in fdf.columns:
    fdf = fdf[fdf["CarAlias - Info"] == car_sel]
if sess_sel and "SessionName - Info" in fdf.columns:
    fdf = fdf[fdf["SessionName - Info"].isin(sess_sel)]
if drv_sel and "DriverName - Info" in fdf.columns:
    fdf = fdf[fdf["DriverName - Info"].isin(drv_sel)]

# Métricas disponíveis
metric_cols = numeric_metric_columns(fdf)
if not metric_cols:
    st.error("Não encontrei colunas numéricas para plot.")
    st.stop()

# Garantir que os defaults existam (fallback para a 1ª métrica numérica)
line_defaults = [m if m in metric_cols else metric_cols[0] for m in DEFAULT_LINE_METRICS]
scatter_default_x = SCATTER_DEFAULT_X if SCATTER_DEFAULT_X in metric_cols else metric_cols[0]
scatter_default_y = SCATTER_DEFAULT_Y if SCATTER_DEFAULT_Y in metric_cols else metric_cols[0]

st.subheader("Painel de 9 Gráficos (3 × 3)")

# -------- Linha 1 --------
c1, c2, c3 = st.columns(3)
with c1:
    render_card_line(fdf, metric_cols, line_defaults[0], "g1", color_by)
with c2:
    render_card_line(fdf, metric_cols, line_defaults[1], "g2", color_by)
with c3:
    render_card_line(fdf, metric_cols, line_defaults[2], "g3", color_by)

st.divider()

# -------- Linha 2 --------
c4, c5, c6 = st.columns(3)
with c4:
    render_card_line(fdf, metric_cols, line_defaults[3], "g4", color_by)
with c5:
    render_card_line(fdf, metric_cols, line_defaults[4], "g5", color_by)
with c6:
    render_card_line(fdf, metric_cols, line_defaults[5], "g6", color_by)

st.divider()

# -------- Linha 3 --------
c7, c8, c9 = st.columns(3)
with c7:
    render_card_line(fdf, metric_cols, line_defaults[6], "g7", color_by)
with c8:
    render_card_line(fdf, metric_cols, line_defaults[7], "g8", color_by)
with c9:
    # Dispersão (X e Y travados por padrão)
    render_card_scatter(fdf, metric_cols, scatter_default_x, scatter_default_y, "g9", color_by)

# -------- Exportar PDF (apenas linhas; dispersão fica fora para não confundir) --------
st.sidebar.subheader("Exportar Gráficos em PDF")
export_metrics = st.sidebar.multiselect(
    "Selecione métricas (linhas) para exportar:",
    metric_cols, default=line_defaults
)
group_for_pdf = st.sidebar.selectbox("Legenda do PDF (agrupamento):", color_options if color_options else ["(sem)"])
group_for_pdf = group_for_pdf if group_for_pdf in fdf.columns else None

if st.sidebar.button("Exportar PDF"):
    pdf_bytes, pdf_name = export_pdf(fdf, export_metrics, group_for_pdf, car_sel)
    st.sidebar.download_button("Baixar PDF", data=pdf_bytes, file_name=pdf_name, mime="application/pdf")
