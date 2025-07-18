import streamlit as st
import pandas as pd
import plotly.express as px
import os
import itertools
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.image as mpimg
from datetime import datetime

st.set_page_config(layout="wide")
st.image("btz_logo.png", width=1000)
st.title("KPI VITAIS - Análise Dinâmica")

# --- Upload do Excel ---
uploaded_file = st.file_uploader("Escolha a planilha KPI VITAIS:", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    # Identificadores de coluna
    col_session = [col for col in df.columns if "SessionName" in col][0]
    col_lap     = [col for col in df.columns if "Lap" in col][0]
    col_date    = [col for col in df.columns if "SessionDate" in col][0]
    col_car     = [col for col in df.columns if "CarAlias" in col][0]
    col_track   = [col for col in df.columns if "TrackName" in col][0]
    col_run     = [col for col in df.columns if "Run" in col and "Info" in col][0]

    # Campo composto para eixo X
    df['SessionLapDate'] = (
        df[col_date].astype(str) +
        ' | Run ' + df[col_run].astype(str) +
        ' | Lap ' + df[col_lap].astype(str) +
        ' | ' + df[col_session].astype(str) +
        ' | Track ' + df[col_track].astype(str)
    )

    # --- Filtros Gerais ---
    st.sidebar.header("Line Graphic Filters")
    car_alias     = st.sidebar.selectbox("Selecione o CarAlias:", df[col_car].unique())
    track_options = ["VISUALIZAR TODAS AS ETAPAS"] + sorted(df[col_track].dropna().unique().tolist())
    track_sel     = st.sidebar.selectbox("Selecione a Etapa (TrackName):", track_options)
    y_axis        = st.sidebar.selectbox("Selecione a métrica (Y Axis) para o gráfico 1:", list(df.columns[8:41]), key="metric_1")
    y_axis_2      = st.sidebar.selectbox("Selecione a métrica (Y Axis) para o gráfico 2:", list(df.columns[8:41]), key="metric_2")

    # --- Filtros para Gráficos Extras ---
    st.sidebar.header("Extra Graph Filters")
    metrics_extra = {}
    for i in range(1, 7):
        metrics_extra[i] = st.sidebar.selectbox(
            f"Métrica (Y Axis) Gráfico Extra {i}:",
            list(df.columns[8:41]),
            key=f"metric_extra_{i}"
        )

    # Filtrar DataFrame principal
    filtered_df = df[df[col_car] == car_alias]
    if track_sel != "VISUALIZAR TODAS AS ETAPAS":
        filtered_df = filtered_df[filtered_df[col_track] == track_sel]
    filtered_df = filtered_df.sort_values(by=[col_date, col_run, col_lap, col_session, col_track])

    # --- Função auxiliar para plotar linha + stats ---
    def plot_line_with_stats(data, y_metric, title, chart_height):
        fig = px.line(
            data, x="SessionLapDate", y=y_metric, color=col_track,
            markers=True,
            labels={"SessionLapDate": "Date | Run | Lap | Session | Track", y_metric: y_metric, col_track: "Etapa"},
            title=title
        )
        fig.update_layout(
            title_font=dict(size=40, family="Arial", color="white"),
            xaxis=dict(tickangle=90, tickfont=dict(size=7)),
            yaxis=dict(title_font=dict(size=25)),
            height=chart_height,
            legend=dict(orientation="v", x=1.02, y=1, xanchor="left", font=dict(size=8)),
            margin=dict(r=10)
        )

        # stats
        vals = pd.to_numeric(data[y_metric], errors='coerce').dropna()
        if not vals.empty:
            mn, mx = vals.min(), vals.max()
            mn_row = data[data[y_metric] == mn].iloc[0]
            mx_row = data[data[y_metric] == mx].iloc[0]
            fig.add_scatter(
                x=[mn_row["SessionLapDate"]], y=[mn], mode="markers+text",
                marker=dict(color="blue", size=10, symbol="triangle-down"),
                text=[f"Min: {mn:.2f}"], textposition="bottom center"
            )
            fig.add_scatter(
                x=[mx_row["SessionLapDate"]], y=[mx], mode="markers+text",
                marker=dict(color="red", size=10, symbol="triangle-up"),
                text=[f"Max: {mx:.2f}"], textposition="top center"
            )
        return fig, vals

    # --- GRÁFICO 1 e 2 ---
    # Primeiro gráfico
    fig1, vals1 = plot_line_with_stats(filtered_df, y_axis, "First Graph", 700)
    fig2, vals2 = plot_line_with_stats(filtered_df, y_axis_2, "Second Graph", 700)

    col1, col1_stats = st.columns([4, 1])
    with col1:
        st.plotly_chart(fig1, use_container_width=True)
    with col1_stats:
        st.subheader("Stats (G1)")
        st.metric("Min", round(vals1.min(), 2))
        st.metric("Max", round(vals1.max(), 2))
        st.metric("Avg", round(vals1.mean(), 2))

    col2, col2_stats = st.columns([4, 1])
    with col2:
        st.plotly_chart(fig2, use_container_width=True)
    with col2_stats:
        st.subheader("Stats (G2)")
        st.metric("Min", round(vals2.min(), 2))
        st.metric("Max", round(vals2.max(), 2))
        st.metric("Avg", round(vals2.mean(), 2))

    # --- GRÁFICOS EXTRAS ---
    st.header("Gráficos Extras")
    left, right = st.columns(2)
    for idx, col_group in enumerate((left, right), start=0):
        start_i = 1 + idx*3
        end_i = start_i + 3
        with col_group:
            for i in range(start_i, end_i):
                metric = metrics_extra[i]
                fig_e, vals_e = plot_line_with_stats(filtered_df, metric, f"Extra {i}", 400)
                st.plotly_chart(fig_e, use_container_width=True)
                st.subheader(f"Stats (Extra {i})")
                st.metric("Min", round(vals_e.min(), 2))
                st.metric("Max", round(vals_e.max(), 2))
                st.metric("Avg", round(vals_e.mean(), 2))

    # --- GRÁFICO 3: Dispersão ---
    st.sidebar.header("Scatter Graph Filters")
    track_disp = st.sidebar.selectbox("Etapa (TrackName) - Dispersão:", track_options, key="track_disp")
    metric_x = st.sidebar.selectbox("Métrica no eixo X:", list(df.columns[8:]), key="x_disp")
    metric_y = st.sidebar.selectbox("Métrica no eixo Y:", list(df.columns[8:]), key="y_disp")
    show_trendline = st.sidebar.checkbox("Mostrar linha de tendência")

    df_disp = df.copy()
    if track_disp != "VISUALIZAR TODAS AS ETAPAS":
        df_disp = df_disp[df_disp[col_track] == track_disp]
    trendline_option = "ols" if show_trendline else None

    fig3 = px.scatter(
        df_disp, x=metric_x, y=metric_y, color=col_track,
        trendline=trendline_option,
        hover_data=[col_session, col_lap, col_run],
        title="Scatter Plot"
    )
    fig3.update_layout(
        title_font=dict(size=50, family="Arial", color="white"),
        height=600,
        xaxis=dict(tickfont=dict(size=8), title_font=dict(size=30)),
        yaxis=dict(tickfont=dict(size=8), title_font=dict(size=30)),
        legend=dict(orientation="v", x=1.02, y=1, xanchor="left", font=dict(size=10))
    )
    st.plotly_chart(fig3, use_container_width=True)

else:
    st.info("Envie o arquivo para iniciar a análise.")
