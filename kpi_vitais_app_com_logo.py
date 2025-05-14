import streamlit as st
import pandas as pd
import plotly.express as px
import os
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
from streamlit_plotly_events import plotly_events

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
    st.sidebar.header("Filtros")
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
        title=f"{y_axis} por Date/Run/Lap/Session/Track"
    )
    fig.update_layout(
        xaxis=dict(
            tickangle=90,
            tickfont=dict(size=8)
        ),
        height=700,
        legend=dict(
            orientation="v",
            x=1.02,
            y=1,
            xanchor="left",
            font=dict(size=10)
        ),
        margin=dict(r=10),
        dragmode='select'
    )

    selected_points = plotly_events(fig, select_event=True, override_height=700, key="chart1")

    if selected_points:
        x_range = fig['layout']['xaxis']['range'] if 'range' in fig['layout']['xaxis'] else None
    else:
        x_range = None

    # --- GRÁFICO 2 ---
    fig2 = px.line(
        filtered_df,
        x="SessionLapDate",
        y=y_axis_2,
        color=col_track,
        markers=True,
        labels={"SessionLapDate": "Date | Run | Lap | Session | Track", y_axis_2: y_axis_2, col_track: "Etapa"},
        title=f"{y_axis_2} por Date/Run/Lap/Session/Track (Gráfico 2)"
    )
    fig2.update_layout(
        xaxis=dict(
            tickangle=90,
            tickfont=dict(size=8),
            range=x_range
        ),
        height=700,
        legend=dict(
            orientation="v",
            x=1.02,
            y=1,
            xanchor="left",
            font=dict(size=10)
        ),
        margin=dict(r=10)
    )
    st.plotly_chart(fig2, use_container_width=True, key="chart2")

    # --- GRÁFICO 3: Dispersão com filtros dedicados ---
    st.markdown("---")
    st.subheader("Gráfico de Dispersão Personalizado")
    st.sidebar.header("Filtros Dispersão")

    track_options_disp = ["TODAS AS ETAPAS"] + sorted(df[col_track].dropna().unique().tolist())
    track_disp = st.sidebar.selectbox("Etapa (TrackName) - Dispersão:", track_options_disp, key="track_disp")

    metric_x = st.sidebar.selectbox("Métrica no eixo X:", list(df.columns[8:]), key="x_disp")
    metric_y = st.sidebar.selectbox("Métrica no eixo Y:", list(df.columns[8:]), key="y_disp")

    df_disp = df.copy()
    if track_disp != "TODAS AS ETAPAS":
        df_disp = df_disp[df_disp[col_track] == track_disp]

    fig3 = px.scatter(
        df_disp,
        x=metric_x,
        y=metric_y,
        color=col_track,
        trendline="ols",
        hover_data=[col_session, col_lap, col_run],
        title=f"Dispersão: {metric_x} vs {metric_y}"
    )
    fig3.update_layout(
        height=600,
        xaxis=dict(tickfont=dict(size=8)),
        yaxis=dict(tickfont=dict(size=8)),
        legend=dict(
            orientation="v",
            x=1.02,
            y=1,
            xanchor="left",
            font=dict(size=10)
        )
    )
    st.plotly_chart(fig3, use_container_width=True)

else:
    st.info("Envie o arquivo para iniciar a análise.")
