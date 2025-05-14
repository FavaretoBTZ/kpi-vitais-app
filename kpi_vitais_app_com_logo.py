import streamlit as st
import pandas as pd
import plotly.express as px
import os
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt

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

    # --- Filtros ---
    st.sidebar.header("Filtros")
    car_alias = st.sidebar.selectbox("Selecione o CarAlias:", df[col_car].unique())
    track_options = ["VISUALIZAR TODAS AS ETAPAS"] + sorted(df[col_track].dropna().unique().tolist())
    track_selected = st.sidebar.selectbox("Selecione a Etapa (TrackName):", track_options)
    y_axis = st.sidebar.selectbox("Selecione a métrica (Y Axis) para o gráfico 1:", list(df.columns[8:41]), key="metric_1")
    y_axis_2 = st.sidebar.selectbox("Selecione a métrica (Y Axis) para o gráfico 2:", list(df.columns[8:41]), key="metric_2")
    y_axis_scatter = st.sidebar.selectbox("Selecione a métrica para Scatter Plot:", list(df.columns[8:41]), key="scatter_metric")

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
    fig.update_layout(xaxis_tickangle=90, height=700)

    if y_axis == y_axis_2:
        st.warning("Selecione duas métricas diferentes para comparar nos gráficos.")
    else:
        col_plot1, col_stats1 = st.columns([4, 1])
        with col_plot1:
            numeric_values = pd.to_numeric(filtered_df[y_axis], errors='coerce').dropna()
            if not numeric_values.empty:
                min_val = numeric_values.min()
                max_val = numeric_values.max()
                min_row = filtered_df[filtered_df[y_axis] == min_val].iloc[0]
                max_row = filtered_df[filtered_df[y_axis] == max_val].iloc[0]

                fig.add_scatter(
                    x=[min_row["SessionLapDate"]],
                    y=[min_val],
                    mode="markers+text",
                    marker=dict(color="blue", size=12, symbol="triangle-down"),
                    text=[f"Min: {min_val:.2f}"],
                    textposition="bottom center",
                    name="Mínimo"
                )
                fig.add_scatter(
                    x=[max_row["SessionLapDate"]],
                    y=[max_val],
                    mode="markers+text",
                    marker=dict(color="red", size=12, symbol="triangle-up"),
                    text=[f"Max: {max_val:.2f}"],
                    textposition="top center",
                    name="Máximo"
                )
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
        fig2.update_layout(xaxis_tickangle=90, height=700)

        col_plot2, col_stats2 = st.columns([4, 1])
        with col_plot2:
            numeric_values_2 = pd.to_numeric(filtered_df[y_axis_2], errors='coerce').dropna()
            if not numeric_values_2.empty:
                min_val2 = numeric_values_2.min()
                max_val2 = numeric_values_2.max()
                min_row2 = filtered_df[filtered_df[y_axis_2] == min_val2].iloc[0]
                max_row2 = filtered_df[filtered_df[y_axis_2] == max_val2].iloc[0]

                fig2.add_scatter(
                    x=[min_row2["SessionLapDate"]],
                    y=[min_val2],
                    mode="markers+text",
                    marker=dict(color="blue", size=12, symbol="triangle-down"),
                    text=[f"Min: {min_val2:.2f}"],
                    textposition="bottom center",
                    name="Mínimo"
                )
                fig2.add_scatter(
                    x=[max_row2["SessionLapDate"]],
                    y=[max_val2],
                    mode="markers+text",
                    marker=dict(color="red", size=12, symbol="triangle-up"),
                    text=[f"Max: {max_val2:.2f}"],
                    textposition="top center",
                    name="Máximo"
                )
            st.plotly_chart(fig2, use_container_width=True)

        with col_stats2:
            st.subheader("Estatísticas")
            st.metric("Mínimo", round(numeric_values_2.min(), 2))
            st.metric("Máximo", round(numeric_values_2.max(), 2))
            st.metric("Média", round(numeric_values_2.mean(), 2))

        # --- SCATTER PLOT ---
        st.markdown("---")
        st.subheader("Gráfico de Dispersão (Scatter Plot)")
        col1, col2 = st.columns([4, 1])
        with col1:
            scatter_fig = px.scatter(
                filtered_df,
                x="SessionLapDate",
                y=y_axis_scatter,
                color=col_track,
                labels={"SessionLapDate": "Date | Run | Lap | Session | Track", y_axis_scatter: y_axis_scatter, col_track: "Etapa"},
                title=f"Scatter Plot: {y_axis_scatter}"
            )
            scatter_fig.update_layout(xaxis_tickangle=90, height=600)
            st.plotly_chart(scatter_fig, use_container_width=True)

    # --- EXPORTAR PDF ---
    st.sidebar.subheader("Exportar Gráficos em PDF")
    if st.sidebar.button("Exportar Todos KPIs para PDF"):
        pdf_filename = f"{car_alias}_KPIs.pdf"
        output_path = os.path.join("/tmp", pdf_filename)

        with PdfPages(output_path) as pdf:
            for metric in df.columns[8:41]:
                plt.figure(figsize=(14, 7))
                for session_date, group in filtered_df.groupby(col_date):
                    plt.plot(
                        group['SessionLapDate'],
                        group[metric],
                        marker='o',
                        label=session_date.date()
                    )
                plt.title(f"{metric} por Date/Run/Lap/Session/Track")
                plt.xlabel("Date | Run | Lap | Session | Track")
                plt.ylabel(metric)
                plt.xticks(rotation=90)
                plt.grid(axis='y')
                plt.legend(title='Data')
                plt.tight_layout()
                pdf.savefig()
                plt.close()

        with open(output_path, "rb") as file:
            st.sidebar.download_button(
                label="Baixar PDF",
                data=file,
                file_name=pdf_filename,
                mime="application/pdf"
            )

else:
    st.info("Envie o arquivo para iniciar a análise.")

