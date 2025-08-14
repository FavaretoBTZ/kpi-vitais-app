import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(layout="wide")
st.image("btz_logo.png", width=1000)
st.title("KPI VITAIS - Análise Dinâmica")

# -----------------------------
# Helpers
# -----------------------------
def safe_get(colnames, contains, also_contains=None):
    """Retorna a primeira coluna cujo nome contém 'contains' (+ opcional 'also_contains')."""
    if also_contains:
        matches = [c for c in colnames if contains in c and also_contains in c]
    else:
        matches = [c for c in colnames if contains in c]
    return matches[0] if matches else None

def ensure_datetime(series):
    try:
        return pd.to_datetime(series, errors="coerce")
    except Exception:
        return pd.to_datetime(series.astype(str), errors="coerce")

def plot_line_stats(data, metric, title, col_track, xcol="SessionLapDate"):
    fig = px.line(
        data, x=xcol, y=metric, color=col_track, markers=True,
        labels={xcol: "Date | Run | Lap | Session | Track", metric: metric, col_track: "Etapa"},
        title=title
    )
    fig.update_layout(
        height=300,
        title_font=dict(size=20),
        xaxis=dict(tickangle=90, tickfont=dict(size=6)),
        yaxis=dict(title_font=dict(size=15))
    )
    # Estatísticas apenas se houver numéricos válidos
    vals = pd.to_numeric(data[metric], errors="coerce").dropna()
    if not vals.empty:
        mn, mx = vals.min(), vals.max()
        mn_row = data.loc[vals.idxmin()]
        mx_row = data.loc[vals.idxmax()]
        fig.add_scatter(
            x=[mn_row[xcol]], y=[mn], mode="markers+text",
            marker=dict(symbol="triangle-down", size=8), text=[f"Min: {mn:.3f}"], textposition="bottom center"
        )
        fig.add_scatter(
            x=[mx_row[xcol]], y=[mx], mode="markers+text",
            marker=dict(symbol="triangle-up", size=8), text=[f"Max: {mx:.3f}"], textposition="top center"
        )
        stats_text = f"**Stats**: Min={mn:.3f}, Max={mx:.3f}, Avg={vals.mean():.3f}"
    else:
        stats_text = "_Sem dados numéricos válidos para estatísticas_"
    return fig, stats_text

# --- Upload do Excel ---
uploaded_file = st.file_uploader("Escolha a planilha KPI VITAIS:", type=["xlsx"])

if uploaded_file:
    # Ler apenas colunas A até BN para base de dados de métricas
    df = pd.read_excel(uploaded_file, usecols="A:BN")
    df.columns = df.columns.str.strip()

    # Identificar colunas-chave (com proteção)
    col_session = safe_get(df.columns, "SessionName")
    col_lap     = safe_get(df.columns, "Lap")
    col_date    = safe_get(df.columns, "SessionDate")
    col_car     = safe_get(df.columns, "CarAlias")
    col_track   = safe_get(df.columns, "TrackName")
    col_run     = safe_get(df.columns, "Run", "Info")

    required = [col_session, col_lap, col_date, col_car, col_track, col_run]
    missing_labels = ["SessionName","Lap","SessionDate","CarAlias","TrackName","Run Info"]
    missing = [name for name, val in zip(missing_labels, required) if val is None]
    if missing:
        st.error(f"As colunas obrigatórias não foram encontradas: {', '.join(missing)}")
        st.stop()

    # Tipar data
    df[col_date] = ensure_datetime(df[col_date])

    # Criar eixo X composto (string curta para a data)
    df["SessionLapDate"] = (
        df[col_date].dt.strftime("%Y-%m-%d %H:%M") + " | Run " + df[col_run].astype(str)
        + " | Lap " + df[col_lap].astype(str) + " | " + df[col_session].astype(str)
        + " | Track " + df[col_track].astype(str)
    )

    # ---------------- Sidebar: filtros gráficos de linha ----------------
    st.sidebar.header("Line Graphic Filters")

    # Filtros principais
    car_aliases = df[col_car].dropna().unique().tolist()
    if not car_aliases:
        st.error("Nenhum valor em CarAlias.")
        st.stop()

    car_alias = st.sidebar.selectbox("Selecione o CarAlias:", car_aliases)

    track_options = ["VISUALIZAR TODAS AS ETAPAS"] + sorted([t for t in df[col_track].dropna().unique().tolist()])
    track_sel = st.sidebar.selectbox("Selecione a Etapa (TrackName):", track_options)

    # Métricas: restringir às colunas numéricas para evitar quebras
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if not numeric_cols:
        st.error("Não encontrei métricas numéricas nas colunas A:BN.")
        st.stop()

    # --- PRESELEÇÃO para o Gráfico 1: "pOil - Min"
    DEFAULT_METRIC = "pOil - Min"
    try:
        default_idx = next(i for i, c in enumerate(numeric_cols) if str(c).strip() == DEFAULT_METRIC)
    except StopIteration:
        default_idx = 0  # fallback se "pOil - Min" não estiver disponível

    metric1 = st.sidebar.selectbox(
        "Selecione métrica Gráfico 1:",
        numeric_cols,
        index=default_idx,
        key="metric_1"
    )

    # Demais métricas seguem padrão normal
    metric2 = st.sidebar.selectbox("Selecione métrica Gráfico 2:", numeric_cols, key="metric_2")

    extra_metrics = {}
    for i in range(3, 9):
        extra_metrics[i] = st.sidebar.selectbox(
            f"Selecione métrica Gráfico {i}:", numeric_cols, key=f"metric_extra_{i}"
        )

    # ---------------- Scatter separado ----------------
    st.sidebar.header("Scatter Graph Filters")
    track_disp     = st.sidebar.selectbox("Etapa - Scatter:", track_options, key="track_disp")
    metric_x       = st.sidebar.selectbox("Métrica X (Scatter):", numeric_cols, key="x_disp")
    metric_y       = st.sidebar.selectbox("Métrica Y (Scatter):", numeric_cols, key="y_disp")
    show_trendline = st.sidebar.checkbox("Mostrar linha de tendência")

    # ---------------- Filtragem principal ----------------
    filtered_df = df[df[col_car] == car_alias].copy()
    if track_sel != "VISUALIZAR TODAS AS ETAPAS":
        filtered_df = filtered_df[filtered_df[col_track] == track_sel].copy()

    # Ordenação estável
    filtered_df = filtered_df.sort_values(by=[col_date, col_run, col_lap, col_session, col_track], kind="mergesort")

    # Preparar DataFrame para scatter
    df_disp = df.copy()
    if track_disp != "VISUALIZAR TODAS AS ETAPAS":
        df_disp = df_disp[df_disp[col_track] == track_disp].copy()

    # ---------------- Configuração dos 9 gráficos ----------------
    chart_configs = [
        ("line", metric1, "Gráfico 1"),
        ("line", metric2, "Gráfico 2"),
    ] + [
        ("line", extra_metrics[i], f"Gráfico {i}") for i in range(3, 9)
    ] + [("scatter", None, "Scatter Plot")]

    # ---------------- Render 3x3 ----------------
    if filtered_df.empty:
        st.warning("Sem dados após os filtros selecionados (linha). Ajuste o CarAlias/Etapa.")
    if df_disp.empty:
        st.warning("Sem dados após os filtros selecionados (scatter).")

    for row in range(3):
        cols = st.columns(3)
        for col_idx, col in enumerate(cols):
            idx = row * 3 + col_idx
            kind, metric, title = chart_configs[idx]
            with col:
                if kind == "line":
                    if not filtered_df.empty:
                        fig, stats_text = plot_line_stats(filtered_df, metric, title, col_track)
                        st.plotly_chart(fig, use_container_width=True)
                        st.markdown(stats_text)
                    else:
                        st.subheader(title)
                        st.info("Sem dados para este gráfico com os filtros atuais.")
                else:
                    if not df_disp.empty:
                        trend = "ols" if show_trendline else None
                        fig_sc = px.scatter(
                            df_disp, x=metric_x, y=metric_y, color=col_track,
                            trendline=trend,
                            hover_data=[col_session, col_lap, col_run],
                            title=title
                        )
                        fig_sc.update_layout(
                            height=300,
                            title_font=dict(size=20),
                            xaxis=dict(tickfont=dict(size=6)),
                            yaxis=dict(title_font=dict(size=15))
                        )
                        st.plotly_chart(fig_sc, use_container_width=True)
                    else:
                        st.subheader(title)
                        st.info("Sem dados para o scatter com os filtros atuais.")
else:
    st.info("Envie o arquivo para iniciar a análise.")
