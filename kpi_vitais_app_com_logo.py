import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

st.set_page_config(layout="wide")
st.title("KPI VITAIS - Análise Dinâmica")

# ---------- Helpers ----------
DEFAULT_METRICS = [
    "LapTime - Info",
    "Full_Brake_intg -Max",
    "24_Brake_Balance -Avg",
    "Full_throttle_intg -Max",
    "G_Comb -Avg",
    "25_AcLat_Trigger -Avg",
    "25_AcLong_Trigger_Positivo -Avg",
    "CarSpeed -Avg",
    "Total_Brake -Avg",
]

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

    # Eixo X composto
    date_str = df["SessionDate - Info"].dt.strftime("%Y-%m-%d %H:%M").fillna("NA") if "SessionDate - Info" in df.columns else "NA"
    lap_str = df["Lap - Info"].fillna("").astype(str) if "Lap - Info" in df.columns else "NA"
    sess    = df["SessionName - Info"].astype(str) if "SessionName - Info" in df.columns else "NA"
    df["SessionLapDate"] = sess + " | Lap " + lap_str + " | " + date_str

    # Ordenação consistente
    sort_keys = [c for c in ["SessionDate - Info","SessionName - Info","Lap - Info"] if c in df.columns]
    if sort_keys:
        df = df.sort_values(by=sort_keys, kind="mergesort").reset_index(drop=True)

    return df

def numeric_metric_columns(df):
    # considera colunas numéricas para plot (exclui auxiliares)
    candidates = []
    for col in df.columns:
        if col in ["SessionLapDate","SessionDate - Info"]:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            candidates.append(col)
    return candidates

def make_plot(df_plot, metric, color_by):
    fig = px.line(
        df_plot,
        x="SessionLapDate",
        y=metric,
        color=color_by if color_by in df_plot.columns else None,
        markers=True,
        labels={"SessionLapDate":"Session | Lap | Date", metric:metric},
        title=f"{metric} por Session/Lap/Date"
    )
    fig.update_layout(
        xaxis_tickangle=90,
        xaxis_title="Session | Lap | Date",
        yaxis_title=metric,
        legend_title=(color_by or "Grupo").replace(" - Info",""),
        height=420,  # altura menor para caber 3×3 confortavelmente
        margin=dict(l=10, r=10, t=50, b=10)
    )
    return fig

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
            plt.xlabel("Session | Lap | Date")
            plt.ylabel(metric)
            plt.xticks(rotation=90)
            plt.grid(axis="y")
            plt.legend(title=(group_col or "Grupo").replace(" - Info",""))
            plt.gca().xaxis.set_major_locator(MaxNLocator(18))
            plt.tight_layout()
            pdf.savefig()
            plt.close()
    buf.seek(0)
    return buf, f"{car_alias or 'AllCars'}_KPIs.pdf"

# ---------- UI ----------
uploaded = st.file_uploader("Escolha a planilha KPI VITAIS:", type=["xlsx"])

if not uploaded:
    st.info("Envie o arquivo para iniciar a análise.")
    st.stop()

df = load_excel(uploaded)

# Sidebar — filtros globais e agrupamento (legenda) compartilhado
st.sidebar.header("Filtros")
car_values = df["CarAlias - Info"].dropna().unique().tolist() if "CarAlias - Info" in df.columns else []
car_sel = st.sidebar.selectbox("Selecione o CarAlias:", car_values) if car_values else None

sess_values = df["SessionName - Info"].dropna().unique().tolist() if "SessionName - Info" in df.columns else []
sess_sel = st.sidebar.multiselect("Filtrar por SessionName (opcional):", sess_values, default=sess_values)

drv_values = df["DriverName - Info"].dropna().unique().tolist() if "DriverName - Info" in df.columns else []
drv_sel = st.sidebar.multiselect("Filtrar por Driver (opcional):", drv_values, default=drv_values)

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

# Candidatas de métrica
metric_cols = numeric_metric_columns(fdf)
if not metric_cols:
    st.error("Não encontrei colunas numéricas para plot.")
    st.stop()

# Define as 9 métricas padrão (usa fallback se alguma não existir)
defaults = []
for name in DEFAULT_METRICS:
    defaults.append(name if name in metric_cols else metric_cols[0])

st.subheader("Painel de 9 Gráficos (3 × 3)")

# ------ Linha 1 ------
row1 = st.container()
with row1:
    c1, c2, c3 = st.columns(3)
    with c1:
        m1 = st.selectbox("Selecione a métrica (Y Axis) — Gráfico 1", metric_cols, index=metric_cols.index(defaults[0]), key="m1")
        st.plotly_chart(make_plot(fdf, m1, color_by), use_container_width=True)
    with c2:
        m2 = st.selectbox("Selecione a métrica (Y Axis) — Gráfico 2", metric_cols, index=metric_cols.index(defaults[1]), key="m2")
        st.plotly_chart(make_plot(fdf, m2, color_by), use_container_width=True)
    with c3:
        m3 = st.selectbox("Selecione a métrica (Y Axis) — Gráfico 3", metric_cols, index=metric_cols.index(defaults[2]), key="m3")
        st.plotly_chart(make_plot(fdf, m3, color_by), use_container_width=True)

st.divider()

# ------ Linha 2 ------
row2 = st.container()
with row2:
    c4, c5, c6 = st.columns(3)
    with c4:
        m4 = st.selectbox("Selecione a métrica (Y Axis) — Gráfico 4", metric_cols, index=metric_cols.index(defaults[3]), key="m4")
        st.plotly_chart(make_plot(fdf, m4, color_by), use_container_width=True)
    with c5:
        m5 = st.selectbox("Selecione a métrica (Y Axis) — Gráfico 5", metric_cols, index=metric_cols.index(defaults[4]), key="m5")
        st.plotly_chart(make_plot(fdf, m5, color_by), use_container_width=True)
    with c6:
        m6 = st.selectbox("Selecione a métrica (Y Axis) — Gráfico 6", metric_cols, index=metric_cols.index(defaults[5]), key="m6")
        st.plotly_chart(make_plot(fdf, m6, color_by), use_container_width=True)

st.divider()

# ------ Linha 3 ------
row3 = st.container()
with row3:
    c7, c8, c9 = st.columns(3)
    with c7:
        m7 = st.selectbox("Selecione a métrica (Y Axis) — Gráfico 7", metric_cols, index=metric_cols.index(defaults[6]), key="m7")
        st.plotly_chart(make_plot(fdf, m7, color_by), use_container_width=True)
    with c8:
        m8 = st.selectbox("Selecione a métrica (Y Axis) — Gráfico 8", metric_cols, index=metric_cols.index(defaults[7]), key="m8")
        st.plotly_chart(make_plot(fdf, m8, color_by), use_container_width=True)
    with c9:
        m9 = st.selectbox("Selecione a métrica (Y Axis) — Gráfico 9", metric_cols, index=metric_cols.index(defaults[8]), key="m9")
        st.plotly_chart(make_plot(fdf, m9, color_by), use_container_width=True)

# ------ Exportar PDF ------
st.sidebar.subheader("Exportar Gráficos em PDF")
export_metrics = st.sidebar.multiselect("Selecione métricas para exportar:", metric_cols, default=list(dict.fromkeys(defaults)))
group_for_pdf = st.sidebar.selectbox("Legenda do PDF (agrupamento):", color_options if color_options else ["(sem)"])
group_for_pdf = group_for_pdf if group_for_pdf in fdf.columns else None

if st.sidebar.button("Exportar PDF"):
    pdf_bytes, pdf_name = export_pdf(fdf, export_metrics, group_for_pdf, car_sel)
    st.sidebar.download_button("Baixar PDF", data=pdf_bytes, file_name=pdf_name, mime="application/pdf")
