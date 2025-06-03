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

    col_session = [col for col in df.columns if "SessionName" in col][0]
    col_lap = [col for col in df.columns if "Lap" in col][0]
    col_date = [col for col in df.columns if "SessionDate" in col][0]
    col_car = [col for col in df.columns if "CarAlias" in col][0]
    col_track = [col for col in df.columns if "TrackName" in col][0]
    col_run = [col for col in df.columns if "Run" in col and "Info" in col][0]

    df['SessionLapDate'] = (
        df[col_date].astype(str) +
        ' | Run ' + df[col_run].astype(str) +
        ' | Lap ' + df[col_lap].astype(str) +
        ' | ' + df[col_session].astype(str) +
        ' | Track ' + df[col_track].astype(str)
    )

    # --- Filtros Gerais ---
    st.sidebar.header("Line Graphic Filters")
    car_alias = st.sidebar.selectbox("Selecione o CarAlias:", df[col_car].unique())
    track_options = ["VISUALIZAR TODAS AS ETAPAS"] + sorted(df[col_track].dropna().unique().tolist())
    track_selected = st.sidebar.selectbox("Selecione a Etapa (TrackName):", track_options)
    y_axis = st.sidebar.selectbox("Selecione a métrica (Y Axis) para o gráfico 1:", list(df.columns[8:41]), key="metric_1")
    y_axis_2 = st.sidebar.selectbox("Selecione a métrica (Y Axis) para o gráfico 2:", list(df.columns[8:41]), key="metric_2")

    filtered_df = df[df[col_car] == car_alias]
    if track_selected != "VISUALIZAR TODAS AS ETAPAS":
        filtered_df = filtered_df[filtered_df[col_track] == track_selected]
    filtered_df = filtered_df.sort_values(by=[col_date, col_run, col_lap, col_session, col_track])

    # --- GRÁFICO 1 ---
    fig = px.line(
        filtered_df,
        x="SessionLapDate",
        y=y_axis,
        color=col_track,
        markers=True,
        labels={"SessionLapDate": "Date | Run | Lap | Session | Track", y_axis: y_axis, col_track: "Etapa"},
        title="First Graph"
    )
    fig.update_layout(
        title_font=dict(size=50, family="Arial", color="white"),
        xaxis=dict(tickangle=90, tickfont=dict(size=8), title_font=dict(size=30)),
        yaxis=dict(title_font=dict(size=30)),
        height=700,
        legend=dict(orientation="v", x=1.02, y=1, xanchor="left", font=dict(size=10)),
        margin=dict(r=10)
    )

    col_plot1, col_stats1 = st.columns([4, 1])
    with col_plot1:
        numeric_values = pd.to_numeric(filtered_df[y_axis], errors='coerce').dropna()
        if not numeric_values.empty:
            min_val = numeric_values.min()
            max_val = numeric_values.max()
            min_row = filtered_df[filtered_df[y_axis] == min_val].iloc[0]
            max_row = filtered_df[filtered_df[y_axis] == max_val].iloc[0]

            fig.add_scatter(x=[min_row["SessionLapDate"]], y=[min_val], mode="markers+text",
                            marker=dict(color="blue", size=12, symbol="triangle-down"),
                            text=[f"Min: {min_val:.2f}"], textposition="bottom center", name="Mínimo")
            fig.add_scatter(x=[max_row["SessionLapDate"]], y=[max_val], mode="markers+text",
                            marker=dict(color="red", size=12, symbol="triangle-up"),
                            text=[f"Max: {max_val:.2f}"], textposition="top center", name="Máximo")
        st.plotly_chart(fig, use_container_width=True)

    with col_stats1:
        st.subheader("Statistic")
        st.markdown("<h3>Minimum</h3>", unsafe_allow_html=True)
        st.metric("", round(numeric_values.min(), 2))
        st.markdown("<h3>Maximum</h3>", unsafe_allow_html=True)
        st.metric("", round(numeric_values.max(), 2))
        st.markdown("<h3>Average</h3>", unsafe_allow_html=True)
        st.metric("", round(numeric_values.mean(), 2))

    # --- GRÁFICO 2 ---
    fig2 = px.line(
        filtered_df,
        x="SessionLapDate",
        y=y_axis_2,
        color=col_track,
        markers=True,
        labels={"SessionLapDate": "Date | Run | Lap | Session | Track", y_axis_2: y_axis_2, col_track: "Etapa"},
        title="Second Graph"
    )
    fig2.update_layout(
        title_font=dict(size=50, family="Arial", color="white"),
        xaxis=dict(tickangle=90, tickfont=dict(size=8), title_font=dict(size=30)),
        yaxis=dict(title_font=dict(size=30)),
        height=700,
        legend=dict(orientation="v", x=1.02, y=1, xanchor="left", font=dict(size=10)),
        margin=dict(r=10)
    )

    col_plot2, col_stats2 = st.columns([4, 1])
    with col_plot2:
        numeric_values_2 = pd.to_numeric(filtered_df[y_axis_2], errors='coerce').dropna()
        if not numeric_values_2.empty:
            min_val2 = numeric_values_2.min()
            max_val2 = numeric_values_2.max()
            min_row2 = filtered_df[filtered_df[y_axis_2] == min_val2].iloc[0]
            max_row2 = filtered_df[filtered_df[y_axis_2] == max_val2].iloc[0]

            fig2.add_scatter(x=[min_row2["SessionLapDate"]], y=[min_val2], mode="markers+text",
                             marker=dict(color="blue", size=12, symbol="triangle-down"),
                             text=[f"Min: {min_val2:.2f}"], textposition="bottom center", name="Mínimo")
            fig2.add_scatter(x=[max_row2["SessionLapDate"]], y=[max_val2], mode="markers+text",
                             marker=dict(color="red", size=12, symbol="triangle-up"),
                             text=[f"Max: {max_val2:.2f}"], textposition="top center", name="Máximo")
        st.plotly_chart(fig2, use_container_width=True)

    with col_stats2:
        st.subheader("Statistic")
        st.markdown("<h4>Minimum</h4>", unsafe_allow_html=True)
        st.metric("", round(numeric_values_2.min(), 2))
        st.markdown("<h4>Maximum</h4>", unsafe_allow_html=True)
        st.metric("", round(numeric_values_2.max(), 2))
        st.markdown("<h4>Average</h4>", unsafe_allow_html=True)
        st.metric("", round(numeric_values_2.mean(), 2))

    # --- GRÁFICO 3: Dispersão ---
    st.sidebar.header("Scatter Graph Filters")

    track_options_disp = ["VISUALIZAR TODAS AS ETAPAS"] + sorted(df[col_track].dropna().unique().tolist())
    track_disp = st.sidebar.selectbox("Etapa (TrackName) - Dispersão:", track_options_disp, key="track_disp")

    metric_x = st.sidebar.selectbox("Métrica no eixo X:", list(df.columns[8:]), key="x_disp")
    metric_y = st.sidebar.selectbox("Métrica no eixo Y:", list(df.columns[8:]), key="y_disp")
    show_trendline = st.sidebar.checkbox("Mostrar linha de tendência")

    df_disp = df.copy()
    if track_disp != "VISUALIZAR TODAS AS ETAPAS":
        df_disp = df_disp[df_disp[col_track] == track_disp]

    trendline_option = "ols" if show_trendline else None

    fig3 = px.scatter(
        df_disp,
        x=metric_x,
        y=metric_y,
        color=col_track,
        trendline=trendline_option,
        hover_data=[col_session, col_lap, col_run],
        title="Scatter Plot"
    )

    fig3.update_layout(
        title_font=dict(size=80, family="Arial", color="white"),
        height=600,
        xaxis=dict(tickfont=dict(size=8), title_font=dict(size=30)),
        yaxis=dict(tickfont=dict(size=8), title_font=dict(size=30)),
        legend=dict(orientation="v", x=1.02, y=1, xanchor="left", font=dict(size=10))
    )

    st.plotly_chart(fig3, use_container_width=True)

else:
    st.info("Envie o arquivo para iniciar a análise.")
