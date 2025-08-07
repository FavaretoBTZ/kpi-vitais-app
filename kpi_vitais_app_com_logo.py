import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(layout="wide")
st.image("btz_logo.png", width=1000)
st.title("KPI VITAIS - Análise Dinâmica")

# --- Upload do Excel ---
uploaded_file = st.file_uploader("Escolha a planilha KPI VITAIS:", type=["xlsx"])
if uploaded_file:
    # Ler apenas colunas A até BN para base de dados de métricas
    df = pd.read_excel(uploaded_file, usecols="A:BN")
    df.columns = df.columns.str.strip()

    # Identificar colunas-chave
    col_session = [c for c in df.columns if "SessionName" in c][0]
    col_lap     = [c for c in df.columns if "Lap" in c][0]
    col_date    = [c for c in df.columns if "SessionDate" in c][0]
    col_car     = [c for c in df.columns if "CarAlias" in c][0]
    col_track   = [c for c in df.columns if "TrackName" in c][0]
    col_run     = [c for c in df.columns if "Run" in c and "Info" in c][0]

    # Criar eixo X composto
    df["SessionLapDate"] = (
        df[col_date].astype(str) + " | Run " + df[col_run].astype(str)
        + " | Lap " + df[col_lap].astype(str) + " | " + df[col_session].astype(str)
        + " | Track " + df[col_track].astype(str)
    )

    # --- Sidebar: filtros gráficos de linha ---
    st.sidebar.header("Line Graphic Filters")
    car_alias = st.sidebar.selectbox("Selecione o CarAlias:", df[col_car].unique())
    track_options = ["VISUALIZAR TODAS AS ETAPAS"] + sorted(df[col_track].dropna().unique().tolist())
    track_sel = st.sidebar.selectbox("Selecione a Etapa (TrackName):", track_options)

    # Seleção de métricas para Gráficos 1 a 8
    metric1 = st.sidebar.selectbox("Selecione métrica Gráfico 1:", list(df.columns[8:]), key="metric_1")
    metric2 = st.sidebar.selectbox("Selecione métrica Gráfico 2:", list(df.columns[8:]), key="metric_2")
    extra_metrics = {}
    for i in range(3, 9):
        extra_metrics[i] = st.sidebar.selectbox(
            f"Selecione métrica Gráfico {i}:", list(df.columns[8:]), key=f"metric_extra_{i}"
        )

    # Scatter filters continuam separados
    st.sidebar.header("Scatter Graph Filters")
    track_disp     = st.sidebar.selectbox("Etapa - Scatter:", track_options, key="track_disp")
    metric_x       = st.sidebar.selectbox("Métrica X (Scatter):", list(df.columns[8:]), key="x_disp")
    metric_y       = st.sidebar.selectbox("Métrica Y (Scatter):", list(df.columns[8:]), key="y_disp")
    show_trendline = st.sidebar.checkbox("Mostrar linha de tendência")

    # Filtrar DataFrame principal
    filtered_df = df[df[col_car] == car_alias]
    if track_sel != "VISUALIZAR TODAS AS ETAPAS":
        filtered_df = filtered_df[filtered_df[col_track] == track_sel]
    filtered_df = filtered_df.sort_values(by=[col_date, col_run, col_lap, col_session, col_track])

    # Preparar DataFrame para scatter
    df_disp = df.copy()
    if track_disp != "VISUALIZAR TODAS AS ETAPAS":
        df_disp = df_disp[df_disp[col_track] == track_disp]

    # Função helper para plot de linha com stats
    def plot_line_stats(data, metric, title):
        fig = px.line(
            data, x="SessionLapDate", y=metric, color=col_track, markers=True,
            labels={"SessionLapDate": "Date | Run | Lap | Session | Track", metric: metric, col_track: "Etapa"},
            title=title
        )
        fig.update_layout(
            height=300,
            title_font=dict(size=20),
            xaxis=dict(tickangle=90, tickfont=dict(size=6)),
            yaxis=dict(title_font=dict(size=15))
        )
        vals = pd.to_numeric(data[metric], errors="coerce").dropna()
        if not vals.empty:
            mn, mx = vals.min(), vals.max()
            mn_row = data[data[metric] == mn].iloc[0]
            mx_row = data[data[metric] == mx].iloc[0]
            fig.add_scatter(
                x=[mn_row["SessionLapDate"]], y=[mn], mode="markers+text",
                marker=dict(symbol="triangle-down", size=8), text=[f"Min: {mn:.2f}"], textposition="bottom center"
            )
            fig.add_scatter(
                x=[mx_row["SessionLapDate"]], y=[mx], mode="markers+text",
                marker=dict(symbol="triangle-up", size=8), text=[f"Max: {mx:.2f}"], textposition="top center"
            )
        return fig, vals

    # Configuração dos 9 gráficos
    chart_configs = [
        ("line", metric1, "Gráfico 1"),
        ("line", metric2, "Gráfico 2"),
    ] + [
        ("line", extra_metrics[i], f"Gráfico {i}") for i in range(3, 9)
    ] + [("scatter", None, "Scatter Plot")]

    # Exibir 3x3 grid
    for row in range(3):
        cols = st.columns(3)
        for col_idx, col in enumerate(cols):
            idx = row * 3 + col_idx
            kind, metric, title = chart_configs[idx]
            with col:
                if kind == "line":
                    fig, vals = plot_line_stats(filtered_df, metric, title)
                    st.plotly_chart(fig, use_container_width=True)
                    st.markdown(f"**Stats**: Min={vals.min():.2f}, Max={vals.max():.2f}, Avg={vals.mean():.2f}")
                else:
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
    st.info("Envie o arquivo para iniciar a análise.")



