import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

st.set_page_config(layout="wide")
st.title("KPI VITAIS - Análise Dinâmica")

# =========================
# Helpers
# =========================
PREFERRED_DEFAULTS = [
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
    # Normaliza tipos essenciais
    if "SessionDate - Info" in df.columns:
        df["SessionDate - Info"] = to_datetime_safe(df["SessionDate - Info"])
    if "Lap - Info" in df.columns:
        df["Lap - Info"] = pd.to_numeric(df["Lap - Info"], errors="coerce").astype("Int64")

    # Coluna composta para o eixo X
    date_str = df["SessionDate - Info"].dt.strftime("%Y-%m-%d %H:%M").fillna("NA") if "SessionDate - Info" in df.columns else "NA"
    lap_str = df["Lap - Info"].astype(str) if "Lap - Info" in df.columns else "NA"
    sess = df["SessionName - Info"].astype(str) if "SessionName - Info" in df.columns else "NA"
    df["SessionLapDate"] = sess + " | Lap " + lap_str + " | " + date_str

    # Ordenação consistente
    sort_keys = [c for c in ["SessionDate - Info", "SessionName - Info", "Lap - Info"] if c in df.columns]
    if sort_keys:
        df = df.sort_values(by=sort_keys, kind="mergesort").reset_index(drop=True)

    return df

def numeric_metric_columns(df):
    num_cols = []
    for col in df.columns:
        if col in ["SessionLapDate", "SessionDate - Info"]:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            num_cols.append(col)
    return num_cols

def safe_unique(series):
    try:
        return series.dropna().unique().tolist()
    except Exception:
        return []

def make_plot(filtered_df, y_axis, color_by, title):
    fig = px.line(
        filtered_df,
        x="SessionLapDate",
        y=y_axis,
        color=color_by if color_by in filtered_df.columns else None,
        markers=True,
        labels={
            "SessionLapDate": "Session | Lap | Date",
            y_axis: y_axis,
            (color_by or "Grupo"): (color_by or "Grupo").replace(" - Info", "")
        },
        title=title
    )
    fig.update_layout(
        xaxis_tickangle=90,
        xaxis_title="Session | Lap | Date",
        yaxis_title=y_axis,
        legend_title=(color_by or "Grupo").replace(" - Info", ""),
        height=600,
        margin=dict(l=10, r=10, t=60, b=10)
    )
    return fig

def export_pdf(filtered_df, metrics, group_col, car_alias):
    buf = BytesIO()
    with PdfPages(buf) as pdf:
        for metric in metrics:
            plt.figure(figsize=(14, 7))
            if group_col in filtered_df.columns:
                groups = filtered_df.groupby(group_col, dropna=False)
            else:
                groups = [("All", filtered_df)]

            for name, group in groups if hasattr(groups, "groups") else groups:
                y = pd.to_numeric(group[metric], errors="coerce")
                x = group["SessionLapDate"].astype(str)
                plt.plot(x, y, marker='o', label=str(name) if name is not pd.NaT else "NA")

            plt.title(f"{metric} por Session/Lap/Date")
            plt.xlabel("Session | Lap | Date")
            plt.ylabel(metric)
            plt.xticks(rotation=90)
            plt.grid(axis='y')
            plt.legend(title=group_col.replace(" - Info", "") if group_col else "Grupo", loc="best")
            ax = plt.gca()
            ax.xaxis.set_major_locator(MaxNLocator(20))
            plt.tight_layout()
            pdf.savefig()
            plt.close()

    pdf_filename = f"{car_alias}_KPIs.pdf"
    buf.seek(0)
    return buf, pdf_filename

def get_default_index(options, target_name):
    """Retorna o índice de 'target_name' nas opções se existir, senão 0."""
    try:
        return options.index(target_name)
    except Exception:
        return 0 if options else 0

# =========================
# UI
# =========================
uploaded_file = st.file_uploader("Escolha a planilha KPI VITAIS:", type=["xlsx"])

if uploaded_file is not None:
    df = load_excel(uploaded_file)

    # ===== Sidebar Filtros =====
    st.sidebar.header("Filtros")

    # CarAlias
    car_alias_values = safe_unique(df["CarAlias - Info"]) if "CarAlias - Info" in df.columns else []
    car_alias = st.sidebar.selectbox("Selecione o CarAlias:", car_alias_values) if car_alias_values else None

    # SessionName opcional
    session_values = safe_unique(df["SessionName - Info"]) if "SessionName - Info" in df.columns else []
    selected_sessions = st.sidebar.multiselect("Filtrar por SessionName (opcional):", session_values, default=session_values)

    # Driver opcional
    driver_values = safe_unique(df["DriverName - Info"]) if "DriverName - Info" in df.columns else []
    selected_drivers = st.sidebar.multiselect("Filtrar por Driver (opcional):", driver_values, default=driver_values if driver_values else [])

    # Coluna para color/legenda (compartilhada pelos 9 gráficos)
    color_options = [c for c in ["SessionDate - Info", "SessionName - Info", "DriverName - Info"] if c in df.columns]
    color_by = st.sidebar.selectbox("Agrupar por (legenda) nos gráficos:", color_options) if color_options else None

    # ===== Aplicar filtros =====
    filtered_df = df.copy()
    if car_alias is not None and "CarAlias - Info" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["CarAlias - Info"] == car_alias]
    if selected_sessions and "SessionName - Info" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["SessionName - Info"].isin(selected_sessions)]
    if selected_drivers and "DriverName - Info" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["DriverName - Info"].isin(selected_drivers)]

    # Reordena de novo pós-filtro
    sort_keys = [c for c in ["SessionDate - Info", "SessionName - Info", "Lap - Info"] if c in filtered_df.columns]
    if sort_keys and not filtered_df.empty:
        filtered_df = filtered_df.sort_values(by=sort_keys, kind="mergesort")

    # Candidatas numéricas
    metric_candidates = numeric_metric_columns(filtered_df)
    if not metric_candidates:
        st.error("Não foram encontradas colunas numéricas para plotar.")
        st.stop()

    # ===== Grade 3x3 de gráficos (cada um com seu próprio seletor de métrica) =====
    st.subheader("Painel de 9 Gráficos (3 × 3)")

    # Descobrir índices padrão para os 9 gráficos usando PREFERRED_DEFAULTS se estiverem disponíveis
    default_indices = []
    for name in PREFERRED_DEFAULTS:
        default_indices.append(get_default_index(metric_candidates, name))
    # Se faltarem entradas (caso menos de 9 preferidas existam na planilha), completa com 0
    while len(default_indices) < 9:
        default_indices.append(0)

    # Renderiza 3 linhas × 3 colunas
    chart_count = 0
    for row in range(3):
        cols = st.columns(3)
        for col in cols:
            with col:
                metric_key = f"metric_select_{chart_count}"
                # Selectbox individual para cada gráfico
                selected_metric = st.selectbox(
                    f"Selecione a métrica (Y Axis) — Gráfico {chart_count+1}",
                    metric_candidates,
                    index=default_indices[chart_count] if chart_count < len(default_indices) else 0,
                    key=metric_key
                )
                # Plot individual
                fig = make_plot(
                    filtered_df,
                    selected_metric,
                    color_by,
                    title=f"{selected_metric} por Session/Lap/Date"
                )
                st.plotly_chart(fig, use_container_width=True)
                chart_count += 1

    # ===== Exportar PDF =====
    st.sidebar.subheader("Exportar Gráficos em PDF")
    export_metrics = st.sidebar.multiselect(
        "Selecione métricas para exportar:",
        metric_candidates,
        default=metric_candidates
    )
    group_for_pdf = st.sidebar.selectbox(
        "Legenda do PDF (agrupamento):",
        color_options if color_options else ["(sem agrupamento)"]
    )
    group_for_pdf = group_for_pdf if group_for_pdf in filtered_df.columns else None

    if st.sidebar.button("Exportar PDF"):
        if not export_metrics:
            st.sidebar.error("Selecione pelo menos uma métrica.")
        else:
            pdf_bytes, pdf_filename = export_pdf(filtered_df, export_metrics, group_for_pdf, car_alias or "AllCars")
            st.sidebar.download_button(
                label="Baixar PDF",
                data=pdf_bytes,
                file_name=pdf_filename,
                mime="application/pdf"
            )
else:
    st.info("Envie o arquivo para iniciar a análise.")
