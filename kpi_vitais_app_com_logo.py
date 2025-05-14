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
    st.sidebar.header("FILTROS GRÁFICOS DE LINHAS")
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
        xaxis=dict(tickangle=90, tickfont=dict(size=8)),
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

            fig.add_scatter(x=[min_row["SessionLapDate"]], y=[min_val], mode="markers+text", marker=dict(color="blue", size=12, symbol="triangle-down"), text=[f"Min: {min_val:.2f}"], textposition="bottom center", name="Mínimo")
            fig.add_scatter(x=[max_row["SessionLapDate"]], y=[max_val], mode="markers+text", marker=dict(color="red", size=12, symbol="triangle-up"), text=[f"Max: {max_val:.2f}"], textposition="top center", name="Máximo")
        st.plotly_chart(fig, use_container_width=True)

    with col_stats1:
        st.subheader("Estatísticas")
        st.metric("Mínimo", round(numeric_values.min(), 2))
        st.metric("Máximo", round(numeric_values.max(), 2))
        st.metric("Média", round(numeric_values.mean(), 2))

    # --- GRÁFICO 2 ---
    st.markdown("---")
    st.subheader("Segundo Gráfico Dinâmico")

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
        xaxis=dict(tickangle=90, tickfont=dict(size=8)),
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

            fig2.add_scatter(x=[min_row2["SessionLapDate"]], y=[min_val2], mode="markers+text", marker=dict(color="blue", size=12, symbol="triangle-down"), text=[f"Min: {min_val2:.2f}"], textposition="bottom center", name="Mínimo")
            fig2.add_scatter(x=[max_row2["SessionLapDate"]], y=[max_val2], mode="markers+text", marker=dict(color="red", size=12, symbol="triangle-up"), text=[f"Max: {max_val2:.2f}"], textposition="top center", name="Máximo")
        st.plotly_chart(fig2, use_container_width=True)

    with col_stats2:
        st.subheader("Estatísticas")
        st.metric("Mínimo", round(numeric_values_2.min(), 2))
        st.metric("Máximo", round(numeric_values_2.max(), 2))
        st.metric("Média", round(numeric_values_2.mean(), 2))

     # --- GRÁFICO 3: Dispersão com filtros dedicados ---
    st.markdown("---")
    st.subheader("Gráfico de Dispersão Personalizado")
    st.sidebar.header("FILTROS GRÁFICO DE DISPERSÃO")

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

    # --- Exportar gráficos para PDF ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("Exportar gráficos")
    exportar_pdf = st.sidebar.button("Exportar gráficos para PDF")

    if exportar_pdf:
        logo_img = mpimg.imread("btz_logo.png")
        data_str = datetime.now().strftime("%d-%m-%Y")
        output_dir = r"C:\Users\vitor\OneDrive\Área de Trabalho\MotorSport\BTZ\Corrida\2025\25ET1\PDF's"
        os.makedirs(output_dir, exist_ok=True)
        pdf_path = os.path.join(output_dir, f"graficos_kpi_possiveis_{data_str}.pdf")

        with PdfPages(pdf_path) as pdf:
            # Capa
            fig_capa = plt.figure(figsize=(11.69, 8.27))  # A4 landscape
            ax = fig_capa.add_subplot(111)
            ax.axis('off')

            imagebox = OffsetImage(logo_img, zoom=1.5)
            ab = AnnotationBbox(imagebox, (0.5, 0.6), frameon=False, box_alignment=(0.5, 0.5))
            ax.add_artist(ab)

            ax.text(0.5, 0.25, "Car Life - Vital #276", fontsize=20, ha="center")
            ax.text(0.99, 0.05, "Engenheiros: Vitor Favareto Nunes", fontsize=10, ha="right")
            ax.text(0.99, 0.01, "Matheus Syx", fontsize=10, ha="right")

            pdf.savefig(fig_capa)
            plt.close()

            # Gráficos de linha
            colors = itertools.cycle(plt.cm.tab20.colors)
            date_colors = {date: next(colors) for date in df[col_date].unique()}
            df_sorted = df.sort_values(by=[col_date, col_session, col_lap])

            for col in df.columns[8:]:
                plt.figure(figsize=(14, 7))
                for session_date, group in df_sorted.groupby(col_date):
                    y_data = pd.to_numeric(group[col], errors='coerce')
                    x_data = group['SessionLapDate']
                    if y_data.notna().any():
                        plt.plot(x_data, y_data, marker='o', label=str(session_date))
                plt.title(f"Linha: {col} por SessionLapDate")
                plt.xlabel("SessionLapDate")
                plt.ylabel(col)
                plt.xticks(rotation=90)
                plt.grid(True)
                plt.legend()
                plt.tight_layout()
                pdf.savefig()
                plt.close()

        with open(pdf_path, "rb") as f:
            st.sidebar.download_button("Baixar PDF", f, file_name=os.path.basename(pdf_path))

else:
    st.info("Envie o arquivo para iniciar a análise.")
